from flask import Flask, request, jsonify
from core.analysis import analyze_image  # adjust import to your function

app = Flask(__name__)

@app.route("/analyze", methods=["POST"])
def analyze():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    img_bytes = file.read()

    # Call your existing analysis code
    result = analyze_image(img_bytes)  # make sure this returns a dict

    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)
