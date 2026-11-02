"""Secure handling of uploaded images: validation, re-encoding and deletion."""

import re
import uuid
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

# Reject very large images before they are decoded (protects server memory)
MAX_PIXELS = 25_000_000
MIN_SIDE = 64

# Pillow format name -> file extension used when saving
ALLOWED_FORMATS = {"JPEG": "jpg", "PNG": "png"}

# Server-generated file names look like: 12_<32 hex characters>.jpg
FILENAME_PATTERN = re.compile(r"^(\d+)_[0-9a-f]{32}\.(jpg|png)$")

# Make Pillow raise an error for decompression bombs
Image.MAX_IMAGE_PIXELS = MAX_PIXELS


class InvalidImageError(ValueError):
    """Raised when an uploaded file is not an acceptable image."""


def has_allowed_extension(filename, allowed_extensions):
    """Return True if the file name ends with an allowed extension."""
    if not filename or "." not in filename:
        return False
    return filename.rsplit(".", 1)[1].lower() in allowed_extensions


def is_valid_upload_name(filename):
    """Return True if the name matches the server-generated pattern."""
    return bool(filename) and FILENAME_PATTERN.match(filename) is not None


def upload_owner_id(filename):
    """Return the farmer id encoded in an upload file name, or None."""
    match = FILENAME_PATTERN.match(filename or "")
    return int(match.group(1)) if match else None


def save_uploaded_image(file_storage, farmer_id, upload_folder):
    """
    Validate an uploaded image and save a clean copy to the upload folder.

    The file is opened with Pillow to prove it is a real JPEG or PNG, then
    re-encoded. Re-encoding removes EXIF metadata (such as GPS location) and
    any data hidden after the image. The original file name from the user is
    never used; a random name is generated instead.

    Returns the new file name (not the full path).
    Raises InvalidImageError with a user-friendly message on failure.
    """
    stream = file_storage.stream

    try:
        # First pass: structural verification of the file
        stream.seek(0)
        with Image.open(stream) as probe:
            image_format = probe.format
            width, height = probe.size
            if image_format not in ALLOWED_FORMATS:
                raise InvalidImageError("Only JPG and PNG images are accepted.")
            if width * height > MAX_PIXELS:
                raise InvalidImageError(
                    "Image resolution is too large. Please upload a smaller image."
                )
            if min(width, height) < MIN_SIDE:
                raise InvalidImageError(
                    f"Image is too small. Minimum size is {MIN_SIDE}x{MIN_SIDE} pixels."
                )
            probe.verify()

        # Second pass: fully decode the image (verify() leaves it unusable)
        stream.seek(0)
        with Image.open(stream) as image:
            image.load()
            image = ImageOps.exif_transpose(image).convert("RGB")
    except InvalidImageError:
        raise
    except (UnidentifiedImageError, Image.DecompressionBombError):
        raise InvalidImageError(
            "The file is not a valid image. Please upload a JPG or PNG photo."
        )
    except (OSError, SyntaxError, ValueError):
        raise InvalidImageError("The image file is corrupted and cannot be read.")

    extension = ALLOWED_FORMATS[image_format]
    filename = f"{int(farmer_id)}_{uuid.uuid4().hex}.{extension}"
    destination = Path(upload_folder) / filename

    if image_format == "JPEG":
        image.save(destination, format="JPEG", quality=92, optimize=True)
    else:
        image.save(destination, format="PNG", optimize=True)

    return filename


def delete_uploaded_image(filename, upload_folder):
    """Delete an uploaded image if the name is valid and the file exists."""
    if not is_valid_upload_name(filename):
        return False
    path = Path(upload_folder) / filename
    try:
        path.unlink()
    except FileNotFoundError:
        return False
    return True