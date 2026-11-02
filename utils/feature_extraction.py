"""
Traditional machine-vision feature extraction (no deep learning).

The same functions are used for training and for prediction, so the
features always match. Each image becomes one vector made of:

1. HOG features        - shapes and edges
2. Color features      - HSV histograms plus RGB mean and standard deviation
3. Texture features    - LBP histogram plus GLCM statistics
"""

import cv2
import numpy as np
from PIL import Image, ImageOps
from skimage.feature import graycomatrix, graycoprops, hog, local_binary_pattern

from config import Config

# Image size used by the whole pipeline (width, height)
IMAGE_SIZE = tuple(Config.IMAGE_SIZE)

# Increase this number whenever the feature settings below are changed.
# A saved model with a different version is refused and must be retrained.
FEATURE_VERSION = 1

# HOG settings
HOG_ORIENTATIONS = 9
HOG_PIXELS_PER_CELL = (16, 16)
HOG_CELLS_PER_BLOCK = (2, 2)

# Color histogram settings
HIST_BINS = 32

# Local Binary Pattern settings
LBP_POINTS = 8
LBP_RADIUS = 1
LBP_BINS = LBP_POINTS + 2  # "uniform" LBP gives P + 2 distinct codes

# Gray Level Co-occurrence Matrix settings
GLCM_LEVELS = 32
GLCM_DISTANCES = [1, 2]
GLCM_ANGLES = [0, np.pi / 4, np.pi / 2, 3 * np.pi / 4]
GLCM_PROPERTIES = ("contrast", "homogeneity", "energy", "correlation")


def load_image_rgb(path):
    """Read an image file and return it as an RGB uint8 array."""
    try:
        with Image.open(path) as image:
            image = ImageOps.exif_transpose(image).convert("RGB")
            return np.asarray(image, dtype=np.uint8)
    except (OSError, ValueError, SyntaxError) as error:
        raise ValueError(f"Cannot read image: {path}") from error


def preprocess_image(rgb):
    """
    Resize to 128x128 and apply a light Gaussian blur.

    INTER_AREA is the best interpolation for shrinking images and the blur
    reduces camera noise before edges and textures are measured.
    """
    width, height = IMAGE_SIZE
    resized = cv2.resize(
        np.ascontiguousarray(rgb), (width, height), interpolation=cv2.INTER_AREA
    )
    return cv2.GaussianBlur(resized, (3, 3), 0)


def extract_hog_features(gray):
    """Histogram of Oriented Gradients on the grayscale image."""
    return hog(
        gray,
        orientations=HOG_ORIENTATIONS,
        pixels_per_cell=HOG_PIXELS_PER_CELL,
        cells_per_block=HOG_CELLS_PER_BLOCK,
        block_norm="L2-Hys",
        feature_vector=True,
    )


def extract_color_features(rgb):
    """Normalised H, S, V histograms plus RGB mean and standard deviation."""
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    channel_ranges = [(0, 180), (0, 256), (0, 256)]  # OpenCV H is 0-179

    parts = []
    for channel, (low, high) in enumerate(channel_ranges):
        hist = cv2.calcHist([hsv], [channel], None, [HIST_BINS], [low, high])
        hist = hist.flatten()
        total = hist.sum()
        parts.append(hist / total if total > 0 else hist)

    pixels = rgb.reshape(-1, 3).astype(np.float32) / 255.0
    parts.append(pixels.mean(axis=0))
    parts.append(pixels.std(axis=0))
    return np.concatenate(parts)


def extract_texture_features(gray):
    """Uniform LBP histogram plus GLCM contrast, homogeneity, energy, correlation."""
    lbp = local_binary_pattern(gray, LBP_POINTS, LBP_RADIUS, method="uniform")
    lbp_hist = np.bincount(
        lbp.astype(np.int64).ravel(), minlength=LBP_BINS
    ).astype(np.float64)
    lbp_hist /= lbp_hist.sum()

    # GLCM works on a small number of gray levels to stay fast and stable
    step = 256 // GLCM_LEVELS
    quantised = (gray // step).astype(np.uint8)
    glcm = graycomatrix(
        quantised,
        distances=GLCM_DISTANCES,
        angles=GLCM_ANGLES,
        levels=GLCM_LEVELS,
        symmetric=True,
        normed=True,
    )
    # Average over the four angles so the features do not depend on rotation
    glcm_features = [
        graycoprops(glcm, name).mean(axis=1) for name in GLCM_PROPERTIES
    ]
    return np.concatenate([lbp_hist] + glcm_features)


def extract_features_from_array(rgb):
    """Return the combined feature vector for an RGB image array."""
    prepared = preprocess_image(rgb)
    gray = cv2.cvtColor(prepared, cv2.COLOR_RGB2GRAY)

    features = np.concatenate(
        [
            extract_hog_features(gray),
            extract_color_features(prepared),
            extract_texture_features(gray),
        ]
    ).astype(np.float32)

    # A completely flat image can produce NaN in GLCM correlation
    return np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)


def extract_features(path):
    """Load an image file and return its combined feature vector."""
    return extract_features_from_array(load_image_rgb(path))