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



app = Flask(__name__)
CORS(app)
print("Loading HiFi model...")
hifi_model = HiFiModel(verbose=False)
print("✓ HiFi model ready!")


# @app.route("/analyze", methods=["POST"])
# def analyze():
#     file = request.files["file"]
#     img = Image.open(file.stream).convert("L")  # grayscale
#     buffer = BytesIO()
#     img.save(buffer, format="PNG")
#     buffer.seek(0)
#     encoded = base64.b64encode(buffer.read()).decode("utf-8")
#     return jsonify({"image": encoded})  # <-- frontend will decode

def format_time(epoch_time):
    return datetime.fromtimestamp(epoch_time, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

def safe_exif(tag):
    return str(tags.get(tag, "")) or "N/A"

@app.route("/analyze", methods=["POST"])
def analyze():
    file = request.files["file"]

    # Save to a temporary file so HiFi can read it
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        tmp_path = tmp.name
        file.save(tmp_path)

    try:
        # Open the original image to know its size
        img = Image.open(tmp_path).convert("RGB")

        # Run the HiFi model
        results = hifi_model.analyze_image(tmp_path, save_mask=True)

        detection = results["detection"]
        mask_array = results["localization"]["mask"]

        # ---- Normalize mask to 0-1 range ----
        mask_min = mask_array.min()
        mask_max = mask_array.max()
        mask_norm = (mask_array - mask_min) / (mask_max - mask_min + 1e-8)

        # Convert to PIL image and resize to match original
        mask_img = Image.fromarray((mask_norm * 255).astype(np.uint8))
        mask_img = mask_img.resize(img.size, resample=Image.BILINEAR)

        # Encode mask to base64
        buffer = BytesIO()
        mask_img.save(buffer, format="PNG")
        buffer.seek(0)
        encoded_mask = base64.b64encode(buffer.read()).decode("utf-8")

        # ---- Debug output ----
        print(f"Detection output: {detection}")
        print(f"Mask stats -> min: {mask_min} max: {mask_max} "
              f"-> normalized min: {mask_norm.min()} max: {mask_norm.max()}")
        print("Sending mask base64 length:", len(encoded_mask))

        return jsonify({
            "mask": encoded_mask,
            "confidence": float(detection["probability"]),
            "is_forged": bool(detection["is_forged"]),
        })
    finally:
        os.remove(tmp_path)

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
    if "files" not in request.files:
        return jsonify({"error": "No files uploaded"}), 400

    files = request.files.getlist("files")
    print("Batch analyze start. Number of files received:", len(files))
    results = []

    for idx, f in enumerate(files):
        print(f"\nProcessing file {idx + 1}/{len(files)}: {f.filename}")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp_path = tmp.name
            f.save(tmp_path)

        try:
            # Open original for size and encode it
            img = Image.open(tmp_path).convert("RGB")
            buffer_orig = BytesIO()
            img.save(buffer_orig, format="PNG")
            buffer_orig.seek(0)
            encoded_original = base64.b64encode(buffer_orig.read()).decode("utf-8")

            try:
                # Run HiFi model
                res = hifi_model.analyze_image(tmp_path, save_mask=True)
                detection = res.get("detection", {})
                mask_array = res.get("localization", {}).get("mask")
                print(f"Detection output: {detection}")
                print(f"Mask exists? {mask_array is not None}")
            except Exception as e:
                print(f"Error processing {f.filename}: {e}")
                detection = {"probability": 0.0, "is_forged": False}
                mask_array = None

            # Normalize & encode mask if it exists
            encoded_mask = None
            if mask_array is not None:
                mask_min, mask_max = mask_array.min(), mask_array.max()
                mask_norm = mask_array
                if mask_max > mask_min:
                    mask_norm = (mask_array - mask_min) / (mask_max - mask_min)
                mask_img = Image.fromarray((mask_norm * 255).astype(np.uint8))
                mask_img = mask_img.resize(img.size, resample=Image.BILINEAR)
                buffer_mask = BytesIO()
                mask_img.save(buffer_mask, format="PNG")
                buffer_mask.seek(0)
                encoded_mask = base64.b64encode(buffer_mask.read()).decode("utf-8")
                print(f"Encoded mask length: {len(encoded_mask)}")

            # Confidence & forged flag
            confidence = float(detection.get("probability") or 0.0)
            is_forged = bool(detection.get("is_forged", False))

            results.append({
                "filename": f.filename,
                "confidence": confidence,
                "is_forged": is_forged,
                "mask": encoded_mask,
                "original": encoded_original
            })
            print(f"Finished processing {f.filename}: confidence={confidence}, is_forged={is_forged}")

        finally:
            os.remove(tmp_path)

    print("Batch analyze complete. Total results:", len(results))
    return jsonify({"results": results})








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
