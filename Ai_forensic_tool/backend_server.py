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

    # Save to a temporary path so HiFi can read it
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        tmp_path = tmp.name
        file.save(tmp_path)

    try:
        results = hifi_model.analyze_image(tmp_path, save_mask=False)
        detection = results["detection"]
        mask_array = results["localization"]["mask"]  # numpy array (0/1)

        # Convert mask array to a PNG in memory
        mask_img = Image.fromarray((mask_array * 255).astype(np.uint8))
        buffer = BytesIO()
        mask_img.save(buffer, format="PNG")
        buffer.seek(0)
        encoded_mask = base64.b64encode(buffer.read()).decode("utf-8")


        print("Sending mask base64 length:", len(encoded_mask))
        return jsonify({
            "mask": encoded_mask,
            "confidence": float(detection["probability"]),
            "is_forged": bool(detection["is_forged"]),
        })
    finally:
        os.remove(tmp_path)


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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
