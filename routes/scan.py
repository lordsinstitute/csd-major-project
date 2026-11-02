"""Scan blueprint: upload, review, analysis, result page and image serving."""

from datetime import date

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    send_from_directory,
    session,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from database.db import db
from models import DiseaseRecord
from utils.forms import ScanForm
from utils.image_utils import (
    InvalidImageError,
    delete_uploaded_image,
    is_valid_upload_name,
    save_uploaded_image,
    upload_owner_id,
)
from utils.ml_model import (
    ModelNotAvailableError,
    PredictionError,
    is_model_available,
    predict_image,
)
from utils.recommendations import get_disease_info, get_recommendations

scan_bp = Blueprint("scan", __name__)

# Session keys
PENDING_KEY = "pending_scan"   # upload waiting for analysis
RESULT_KEY = "last_result"     # class probabilities of the latest analysis


def _discard_pending():
    """Delete the pending upload (file and session data), if there is one."""
    pending = session.pop(PENDING_KEY, None)
    if not pending:
        return
    filename = pending.get("image_path")
    # Only delete files that belong to the current farmer
    if upload_owner_id(filename) == current_user.id:
        delete_uploaded_image(filename, current_app.config["UPLOAD_FOLDER"])


def get_pending_scan():
    """
    Return the pending scan dictionary for the current farmer, or None.

    The data is dropped if the file is missing or does not belong to the
    logged-in farmer.
    """
    pending = session.get(PENDING_KEY)
    if not pending:
        return None

    filename = pending.get("image_path")
    owner_ok = upload_owner_id(filename) == current_user.id
    file_ok = is_valid_upload_name(filename) and (
        current_app.config["UPLOAD_FOLDER"] / filename
    ).is_file()
    if not (owner_ok and file_ok):
        session.pop(PENDING_KEY, None)
        return None
    return pending


def _find_record(record_id):
    """Return the current farmer's record with this id, or None."""
    return db.session.execute(
        select(DiseaseRecord).filter_by(id=record_id, farmer_id=current_user.id)
    ).scalar_one_or_none()


@scan_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    """Show the upload form and accept a new scan."""
    form = ScanForm()

    if form.validate_on_submit():
        try:
            filename = save_uploaded_image(
                form.image.data,
                current_user.id,
                current_app.config["UPLOAD_FOLDER"],
            )
        except InvalidImageError as error:
            form.image.errors.append(str(error))
        else:
            # A new upload replaces any earlier one that was never analysed
            _discard_pending()
            session[PENDING_KEY] = {
                "batch_name": form.batch_name.data,
                "scan_date": form.scan_date.data.isoformat(),
                "total_birds": form.total_birds.data,
                "sick_birds": form.sick_birds.data,
                "dead_birds": form.dead_birds.data,
                "image_path": filename,
            }
            flash("Image uploaded successfully. Please review the details.", "success")
            return redirect(url_for("scan.review"))

    return render_template("scan/upload.html", form=form)


@scan_bp.route("/upload/review")
@login_required
def review():
    """Show the uploaded image and entered details before analysis."""
    pending = get_pending_scan()
    if pending is None:
        flash("No uploaded image found. Please upload an image.", "warning")
        return redirect(url_for("scan.upload"))

    details = dict(pending)
    details["scan_date"] = date.fromisoformat(pending["scan_date"])
    return render_template(
        "scan/review.html", scan=details, model_ready=is_model_available()
    )


@scan_bp.route("/upload/analyze", methods=["POST"])
@login_required
def analyze():
    """Run the disease prediction, save the record and show the result."""
    pending = get_pending_scan()
    if pending is None:
        flash("No uploaded image found. Please upload an image.", "warning")
        return redirect(url_for("scan.upload"))

    filename = pending["image_path"]

    # Protection against a double click or a re-sent form: one record per image
    existing = db.session.execute(
        select(DiseaseRecord).filter_by(
            farmer_id=current_user.id, image_path=filename
        )
    ).scalar_one_or_none()
    if existing is not None:
        session.pop(PENDING_KEY, None)
        return redirect(url_for("scan.result", record_id=existing.id))

    image_file = current_app.config["UPLOAD_FOLDER"] / filename
    try:
        prediction = predict_image(image_file)
    except ModelNotAvailableError as error:
        flash(str(error), "danger")
        return redirect(url_for("scan.review"))
    except PredictionError as error:
        flash(str(error), "danger")
        return redirect(url_for("scan.review"))

    record = DiseaseRecord(
        farmer_id=current_user.id,
        batch_name=pending["batch_name"],
        total_birds=pending["total_birds"],
        sick_birds=pending["sick_birds"],
        dead_birds=pending["dead_birds"],
        date=date.fromisoformat(pending["scan_date"]),
        image_path=filename,
        predicted_disease=prediction["disease"],
        confidence=prediction["confidence"],
        risk_level=prediction["risk_level"],
    )
    db.session.add(record)
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception("Could not save the disease record")
        flash("The result could not be saved. Please try again.", "danger")
        return redirect(url_for("scan.review"))

    # The record is saved: the upload is no longer pending (the image stays)
    session.pop(PENDING_KEY, None)
    session[RESULT_KEY] = {
        "record_id": record.id,
        "probabilities": prediction["probabilities"],
    }
    flash("Analysis complete. The scan was saved to your history.", "success")
    return redirect(url_for("scan.result", record_id=record.id))


@scan_bp.route("/result/<int:record_id>")
@login_required
def result(record_id):
    """Show the result card for one of the current farmer's scans."""
    record = _find_record(record_id)
    if record is None:
        abort(404)

    # Per-class probabilities are only kept for the scan that was just analysed
    stored = session.get(RESULT_KEY)
    probabilities = None
    if stored and stored.get("record_id") == record.id:
        probabilities = sorted(
            stored["probabilities"].items(), key=lambda item: item[1], reverse=True
        )

    low_confidence = record.confidence < current_app.config["RISK_MEDIUM_THRESHOLD"]
    return render_template(
        "scan/result.html",
        record=record,
        info=get_disease_info(record.predicted_disease),
        recommendations=get_recommendations(record.predicted_disease),
        probabilities=probabilities,
        low_confidence=low_confidence,
    )


@scan_bp.route("/upload/cancel", methods=["POST"])
@login_required
def cancel():
    """Cancel the pending upload and delete its image file."""
    _discard_pending()
    flash("Upload cancelled.", "info")
    return redirect(url_for("scan.upload"))


@scan_bp.route("/uploads/<filename>")
@login_required
def uploaded_file(filename):
    """
    Serve an uploaded image to its owner only.

    The file name must match the server-generated pattern, which also blocks
    path traversal. The farmer id inside the name must match the logged-in
    farmer. Other farmers receive a 404 so file names cannot be probed.
    """
    if not is_valid_upload_name(filename):
        abort(404)
    if upload_owner_id(filename) != current_user.id:
        abort(404)

    response = send_from_directory(
        current_app.config["UPLOAD_FOLDER"], filename, conditional=True
    )
    response.headers["Cache-Control"] = "private, max-age=3600"
    return response