# backend_server.py
import base64
from io import BytesIO
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import os, sys
import tempfile
from metadata_scanner import sha256sum, extract_gps
import exifread
from datetime import datetime, timezone
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "hifi_wrapper")))
from hifi_model import HiFiModel
import numpy as np
from PIL import Image
import numpy as np
import base64
from io import BytesIO
import os, tempfile, base64
import json
import base64, tempfile
from flask import Flask, request, send_file
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
import sqlite3
from flask import request
from functools import wraps
from flask import request, jsonify
import threading

app = Flask(__name__)
CORS(app)
print("Loading HiFi model...")
hifi_model = HiFiModel(verbose=False)
print("✓ HiFi model ready!")

batch_progress = {}


# @app.route("/analyze", methods=["POST"])
# def analyze():
#     file = request.files["file"]
#     img = Image.open(file.stream).convert("L")  # grayscale
#     buffer = BytesIO()
#     img.save(buffer, format="PNG")
#     buffer.seek(0)
#     encoded = base64.b64encode(buffer.read()).decode("utf-8")
#     return jsonify({"image": encoded})  # <-- frontend will decode


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "core", "analysis_logs.db")

def extract_metadata_dict(image_path: str) -> dict:
    """Return a metadata dict for an image file."""
    try:
        stat = os.stat(image_path)
        sha256 = sha256sum(image_path)
        size_bytes = stat.st_size

        with open(image_path, "rb") as f:
            tags = exifread.process_file(f, details=False)

        make       = str(tags.get("Image Make", "")) or None
        model      = str(tags.get("Image Model", "")) or None
        lens       = str(tags.get("EXIF LensModel", "")) or None
        date_taken = str(tags.get("EXIF DateTimeOriginal", "")) or None
        serial     = str(tags.get("EXIF BodySerialNumber", "")) or "N/A"
        software    = str(tags.get("Image Software", "")) or "N/A"
        description = str(tags.get("Image ImageDescription", "")) or "N/A"
        created  = str(tags.get("EXIF DateTimeOriginal", "")) or "N/A"
        modified = str(tags.get("EXIF DateTimeDigitized", "")) or "N/A"
        analysed = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        lat, lon, alt = extract_gps(tags)

        return {
            "sha256": sha256,
            "size_bytes": size_bytes,
            "created": created,
            "modified": modified,
            "analysed": analysed,
            "make": make,
            "model": model,
            "serial": serial,
            "lens": lens,
            "date_taken": date_taken,
            "software": software,
            "description": description,
            "latitude": lat,
            "longitude": lon,
            "altitude": alt,
        }
    except Exception as e:
        print("[DEBUG] Metadata extraction failed:", e)
        return {}


def get_current_user_from_token():
    return {"username": "test_user"}  # temporary stub

def log_analysis(username, filename, confidence, is_forged, metadata, image_b64, mask_b64=None):
    conn = None
    try:
        # ensure metadata is a dict
        if callable(metadata):
            raise TypeError("metadata is a function, not a dict")

        safe_meta = {k: (v() if callable(v) else v) for k, v in metadata.items()}

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO analysis_logs
            (username, filename, confidence, is_forged, metadata, image_base64, mask_base64)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            username,
            filename,
            float(confidence) if confidence is not None else 0.0,
            int(bool(is_forged)),
            json.dumps(safe_meta, default=str),
            image_b64,
            mask_b64
        ))
        conn.commit()
        print(f"[DEBUG] Inserted row for {filename} by {username}")
    except Exception as e:
        print("❌ Failed to log analysis:", e)
    finally:
        if conn:   # ✅ only close if it was successfully opened
            conn.close()






# def get_current_user_from_token():
#     auth = request.headers.get("Authorization")
#     if not auth or not auth.startswith("Bearer "):
#         return None
#     token = auth.replace("Bearer ", "").strip()
#     user = user_manager.validate_session(token)  # your session/token check
#     return user

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user_from_token()
        if not user:
            return jsonify({"error": "Unauthorized"}), 401
        return f(user, *args, **kwargs)  # pass user to the endpoint
    return decorated


# def log_analysis(username, filename, confidence, is_forged, metadata, image_b64, mask_b64=None):
#     conn = sqlite3.connect(DB_PATH)
#     cursor = conn.cursor()

#     cursor.execute("""
#         INSERT INTO analysis_logs
#         (username, filename, confidence, is_forged, metadata, image_base64, mask_base64)
#         VALUES (?, ?, ?, ?, ?, ?, ?)
#     """, (
#         username,
#         filename,
#         confidence,
#         int(is_forged),  # SQLite uses int for boolean
#         json.dumps(metadata),
#         image_b64,
#         mask_b64
#     ))

#     conn.commit()
#     conn.close()

def format_time(epoch_time):
    return datetime.fromtimestamp(epoch_time, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

def safe_exif(tag):
    return str(tags.get(tag, "")) or "N/A"

@app.route("/analyze", methods=["POST"])
@login_required
def analyze(user):
    file = request.files["file"]

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        tmp_path = tmp.name
        file.save(tmp_path)

    try:
        img = Image.open(tmp_path).convert("RGB")

        results = hifi_model.analyze_image(tmp_path, save_mask=True)
        detection = results["detection"]
        mask_array = results["localization"]["mask"]

        # Encode mask
        encoded_mask = None
        if mask_array is not None:
            mask_min, mask_max = mask_array.min(), mask_array.max()
            mask_norm = (mask_array - mask_min) / (mask_max - mask_min + 1e-8)
            mask_img = Image.fromarray((mask_norm * 255).astype(np.uint8))
            mask_img = mask_img.resize(img.size, resample=Image.BILINEAR)
            buffer = BytesIO()
            mask_img.save(buffer, format="PNG")
            buffer.seek(0)
            encoded_mask = base64.b64encode(buffer.read()).decode("utf-8")

        # Encode original image
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        encoded_img = base64.b64encode(buffer.read()).decode("utf-8")

        # Extract metadata
        metadata = extract_metadata(tmp_path)

        # Log to database
        log_analysis(
            username=user["username"],
            filename=file.filename,
            confidence=detection["probability"],
            is_forged=detection["is_forged"],
            metadata = extract_metadata(tmp_path),
            image_b64=encoded_img,
            mask_b64=encoded_mask
        )

        return jsonify({
            "mask": encoded_mask,
            "confidence": float(detection["probability"]),
            "is_forged": bool(detection["is_forged"]),
        })

    finally:
        os.remove(tmp_path)

@app.route("/api/generate-report-from-log/<int:log_id>", methods=["GET"])
def generate_report_from_log(log_id):
    import io, json, base64
    from flask import send_file
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from PIL import Image
    import sqlite3

    # Make sure DB_PATH points to correct file
    DB_PATH = os.path.join(BASE_DIR, "core", "analysis_logs.db")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT username, filename, analysed_at, is_forged, confidence, metadata, image_base64, mask_base64
        FROM analysis_logs WHERE id = ?
    """, (log_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return {"error": "Log entry not found"}, 404

    username, filename, analysed_at, is_forged, confidence, metadata_json, image_b64, mask_b64 = row
    metadata = json.loads(metadata_json) if metadata_json else {}

    confidence_val = float(confidence or 0.0) * 100
    analysed_at = analysed_at or "N/A"

    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>FrameTruth Forensic Report</b>", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"User: {username}", styles["Normal"]))
    story.append(Paragraph(f"Filename: {filename}", styles["Normal"]))
    story.append(Paragraph(f"Analysis Date: {analysed_at}", styles["Normal"]))
    story.append(Paragraph(f"Forgery Detected: {'Yes' if is_forged else 'No'}", styles["Normal"]))
    story.append(Paragraph(f"Confidence: {confidence_val:.1f}%", styles["Normal"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>Metadata:</b>", styles["Heading2"]))
    if metadata:
        for k, v in metadata.items():
            story.append(Paragraph(f"{k}: {v}", styles["Normal"]))
    else:
        story.append(Paragraph("No metadata available.", styles["Normal"]))
    story.append(Spacer(1, 12))

    def image_from_b64(b64data):
        if not b64data:
            return None
        try:
            img_bytes = io.BytesIO(base64.b64decode(b64data))
            pil_img = Image.open(img_bytes)
            out_bytes = io.BytesIO()
            pil_img.save(out_bytes, format="PNG")
            out_bytes.seek(0)
            return RLImage(out_bytes, width=250, height=250)
        except Exception as e:
            print("[DEBUG] Failed to decode image:", e)
            return None

    if image_b64:
        img = image_from_b64(image_b64)
        if img:
            story.append(img)
            story.append(Spacer(1, 12))
    if mask_b64:
        mask_img = image_from_b64(mask_b64)
        if mask_img:
            story.append(mask_img)

    pdf_bytes = io.BytesIO()
    doc = SimpleDocTemplate(pdf_bytes, pagesize=A4)
    doc.build(story)
    pdf_bytes.seek(0)

    return send_file(
        pdf_bytes,
        as_attachment=True,
        download_name="forensic_report.pdf",
        mimetype="application/pdf"
    )






@app.route("/api/generate-report", methods=["POST"])
def generate_report():
    data = request.get_json()
    confidence = data.get("confidence", 0)
    metadata = data.get("metadata", {})
    image_b64 = data.get("image_base64")
    mask_b64 = data.get("mask_base64")

    if not image_b64:
        return {"error": "No image provided"}, 400

    # Decode images to temporary files
    tmp_image = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    tmp_image.write(base64.b64decode(image_b64))
    tmp_image.flush()

    tmp_mask = None
    if mask_b64:
        tmp_mask = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        tmp_mask.write(base64.b64decode(mask_b64))
        tmp_mask.flush()

    # Generate PDF
    tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(tmp_pdf.name, pagesize=A4)
    story = []

    story.append(Paragraph("<b>FrameTruth Forensic Report</b>", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Confidence of Forgery: {confidence*100:.1f}%", styles["Normal"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>Metadata:</b>", styles["Heading2"]))
    for k, v in metadata.items():
        story.append(Paragraph(f"{k}: {v}", styles["Normal"]))
    story.append(Spacer(1, 12))

    story.append(RLImage(tmp_image.name, width=250, height=250))
    story.append(Spacer(1, 12))
    if tmp_mask:
        story.append(RLImage(tmp_mask.name, width=250, height=250))

    doc.build(story)

    return send_file(tmp_pdf.name, as_attachment=True, download_name="forensic_report.pdf")



@app.route("/batch_analyze", methods=["POST"])
def batch_analyze():
    """
    Accept multiple images and return detection info for each.
    Each result includes:
      - filename
      - confidence
      - is_forged
      - mask (base64 PNG) or None
      - original image (base64 PNG) for display
    """
    username = request.headers.get("X-Username")

    if not username:
        return jsonify({"error": "Username header missing"}), 400

    if "files" not in request.files:
        return jsonify({"error": "No files uploaded"}), 400

    files = request.files.getlist("files")
    total_files = len(files)
    print(f"Batch analyze start. Number of files received: {total_files}")

    # ✅ Initialize progress tracking
    batch_progress[username] = {"done": 0, "total": total_files}

    results = []

    for idx, f in enumerate(files):
        print(f"\nProcessing file {idx + 1}/{total_files}: {f.filename}")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp_path = tmp.name
            f.save(tmp_path)

        try:
            img = Image.open(tmp_path).convert("RGB")
            buffer_orig = BytesIO()
            img.save(buffer_orig, format="PNG")
            buffer_orig.seek(0)
            encoded_original = base64.b64encode(buffer_orig.read()).decode("utf-8")

            try:
                res = hifi_model.analyze_image(tmp_path, save_mask=True)
                detection = res.get("detection", {})
                mask_array = res.get("localization", {}).get("mask")
                print(f"Detection output: {detection}")
            except Exception as e:
                print(f"Error processing {f.filename}: {e}")
                detection = {"probability": 0.0, "is_forged": False}
                mask_array = None

            encoded_mask = None
            if mask_array is not None:
                mask_min, mask_max = mask_array.min(), mask_array.max()
                if mask_max > mask_min:
                    mask_norm = (mask_array - mask_min) / (mask_max - mask_min)
                else:
                    mask_norm = mask_array
                mask_img = Image.fromarray((mask_norm * 255).astype(np.uint8))
                mask_img = mask_img.resize(img.size, resample=Image.BILINEAR)
                buffer_mask = BytesIO()
                mask_img.save(buffer_mask, format="PNG")
                buffer_mask.seek(0)
                encoded_mask = base64.b64encode(buffer_mask.read()).decode("utf-8")

            confidence = float(detection.get("probability") or 0.0)
            is_forged = bool(detection.get("is_forged", False))

            meta_dict = extract_metadata_dict(tmp_path)
            log_analysis(
                username=username,
                filename=f.filename,
                confidence=confidence,
                is_forged=is_forged,
                metadata=meta_dict,
                image_b64=encoded_original,
                mask_b64=encoded_mask,
            )

            results.append({
                "filename": f.filename,
                "confidence": confidence,
                "is_forged": is_forged,
                "mask": encoded_mask,
                "original": encoded_original,
            })
            print(f"Finished processing {f.filename}: confidence={confidence}, is_forged={is_forged}")

        finally:
            os.remove(tmp_path)

            # ✅ Increment progress
            batch_progress[username]["done"] += 1
            print(f"Progress: {batch_progress[username]['done']}/{total_files}")

    print("Batch analyze complete. Total results:", len(results))
    return jsonify({"results": results})


@app.route("/logs", methods=["GET"])
def get_logs():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT id, username, analysed_at, filename, is_forged
        FROM analysis_logs
        ORDER BY datetime(analysed_at) DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/batch_progress", methods=["GET"])
def get_batch_progress():
    username = request.headers.get("X-Username")
    if not username:
        return jsonify({"error": "Username header missing"}), 400

    progress = batch_progress.get(username, {"done": 0, "total": 0})
    return jsonify(progress)





@app.route("/metadata", methods=["POST"])
def metadata():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    # Save to a temporary file so exifread can access it
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        tmp_path = tmp.name
        file.save(tmp_path)

    try:
        # File size & hash
        stat = os.stat(tmp_path)
        sha256 = sha256sum(tmp_path)
        size_bytes = stat.st_size

        # EXIF extraction
        with open(tmp_path, "rb") as f:
            tags = exifread.process_file(f, details=False)

        # Camera info
        make       = str(tags.get("Image Make", "")) or None
        model      = str(tags.get("Image Model", "")) or None
        lens       = str(tags.get("EXIF LensModel", "")) or None
        date_taken = str(tags.get("EXIF DateTimeOriginal", "")) or None
        serial     = str(tags.get("EXIF BodySerialNumber", "")) or "N/A" 

        # Software / editing info
        software    = str(tags.get("Image Software", "")) or "N/A"
        description = str(tags.get("Image ImageDescription", "")) or "N/A"

        # File timestamps (fallback to N/A)
        created  = str(tags.get("EXIF DateTimeOriginal", "")) or "N/A"
        modified = str(tags.get("EXIF DateTimeDigitized", "")) or "N/A"
        analysed = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        # GPS
        lat, lon, alt = extract_gps(tags)

        data = {
            "sha256": sha256,
            "size_bytes": size_bytes,
            "created": created,
            "modified": modified,
            "analysed": analysed,
            "make": make,
            "model": model,
            "serial": serial,
            "lens": lens,
            "date_taken": date_taken,
            "software": software,
            "description": description,
            "latitude": lat,
            "longitude": lon,
            "altitude": alt,
        }

        return jsonify(data)

    finally:
        os.remove(tmp_path)

@app.route("/batch_metadata", methods=["POST"])
def batch_metadata():
    """
    Accept multiple images and return metadata info for each.
    Each result includes:
      - filename
      - sha256
      - size_bytes
      - created, modified, analysed
      - make, model, serial, lens, date_taken, software, description
      - latitude, longitude, altitude
    """
    if "files" not in request.files:
        return jsonify({"error": "No files uploaded"}), 400

    files = request.files.getlist("files")
    results = []

    for f in files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp_path = tmp.name
            f.save(tmp_path)

        try:
            # File size & hash
            stat = os.stat(tmp_path)
            sha256 = sha256sum(tmp_path)
            size_bytes = stat.st_size

            # EXIF extraction
            with open(tmp_path, "rb") as file_obj:
                tags = exifread.process_file(file_obj, details=False)

            # Camera info
            make       = str(tags.get("Image Make", "")) or None
            model      = str(tags.get("Image Model", "")) or None
            lens       = str(tags.get("EXIF LensModel", "")) or None
            date_taken = str(tags.get("EXIF DateTimeOriginal", "")) or None
            serial     = str(tags.get("EXIF BodySerialNumber", "")) or "N/A" 

            # Software / editing info
            software    = str(tags.get("Image Software", "")) or "N/A"
            description = str(tags.get("Image ImageDescription", "")) or "N/A"

            # File timestamps (fallback to N/A)
            created  = str(tags.get("EXIF DateTimeOriginal", "")) or "N/A"
            modified = str(tags.get("EXIF DateTimeDigitized", "")) or "N/A"
            analysed = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

            # GPS
            lat, lon, alt = extract_gps(tags)

            results.append({
                "filename": f.filename,
                "sha256": sha256,
                "size_bytes": size_bytes,
                "created": created,
                "modified": modified,
                "analysed": analysed,
                "make": make,
                "model": model,
                "serial": serial,
                "lens": lens,
                "date_taken": date_taken,
                "software": software,
                "description": description,
                "latitude": lat,
                "longitude": lon,
                "altitude": alt,
            })

        finally:
            os.remove(tmp_path)

    return jsonify({"results": results})



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
