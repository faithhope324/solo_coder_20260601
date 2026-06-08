import os
import base64
import numpy as np
import cv2
from flask import Flask, render_template, request, jsonify, Response
from face_detector import FaceDetector
from mask_classifier import MaskClassifier
from camera_stream import CameraStream

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "mask_model.h5")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

face_detector = FaceDetector()
mask_classifier = MaskClassifier(
    model_path=MODEL_PATH if os.path.exists(MODEL_PATH) else None
)
camera_stream = None


def _process_image(image_bytes):
    nparr = np.frombuffer(image_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if frame is None:
        return None, []

    faces = face_detector.detect(frame)
    results = []

    for x, y, w, h in faces:
        roi = frame[y : y + h, x : x + w]
        has_mask, confidence = mask_classifier.predict(roi)
        results.append(
            {
                "box": [int(x), int(y), int(w), int(h)],
                "has_mask": bool(has_mask),
                "confidence": round(float(confidence), 4),
            }
        )

    annotated = FaceDetector.annotate_frame(frame, faces, results)
    _, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 90])
    img_b64 = base64.b64encode(buf).decode("utf-8")

    return img_b64, results


def _build_result(img_b64, results):
    return {
        "image": f"data:image/jpeg;base64,{img_b64}",
        "faces": results,
        "count": len(results),
        "mask_count": sum(1 for r in results if r["has_mask"]),
        "no_mask_count": sum(1 for r in results if not r["has_mask"]),
    }


@app.route("/")
def index():
    mode = "CNN" if mask_classifier.use_cnn else "Heuristic"
    return render_template("index.html", model_status=mode)


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    f = request.files["file"]
    if f.filename == "":
        return jsonify({"error": "No file selected"}), 400

    img_b64, results = _process_image(f.read())
    if img_b64 is None:
        return jsonify({"error": "Invalid image"}), 400

    return jsonify(_build_result(img_b64, results))


@app.route("/camera/start")
def camera_start():
    global camera_stream
    if camera_stream is not None and camera_stream.is_running:
        return jsonify({"status": "already_running"})

    try:
        camera_stream = CameraStream(
            camera_index=0,
            model_path=MODEL_PATH if os.path.exists(MODEL_PATH) else None,
        )
        camera_stream.start()
        return jsonify({"status": "started"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/camera/stop")
def camera_stop():
    global camera_stream
    if camera_stream is not None:
        camera_stream.stop()
        camera_stream = None
    return jsonify({"status": "stopped"})


@app.route("/camera/feed")
def camera_feed():
    global camera_stream
    if camera_stream is None or not camera_stream.is_running:
        return Response("Camera not started", status=400)

    return Response(
        camera_stream.generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@app.route("/camera/capture")
def camera_capture():
    global camera_stream
    if camera_stream is None or not camera_stream.is_running:
        return jsonify({"error": "Camera not started"}), 400

    frame, results = camera_stream.capture_single()
    if frame is None:
        return jsonify({"error": "Capture failed"}), 500

    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
    img_b64 = base64.b64encode(buf).decode("utf-8")
    return jsonify(_build_result(img_b64, results))


@app.route("/model/status")
def model_status_api():
    return jsonify(
        {
            "mode": "CNN" if mask_classifier.use_cnn else "Heuristic",
            "model_loaded": mask_classifier.use_cnn,
            "model_path": MODEL_PATH,
        }
    )


if __name__ == "__main__":
    mode = "CNN" if mask_classifier.use_cnn else "Heuristic (no trained model)"
    print("=" * 50)
    print("  Mask Detection System")
    print(f"  Mode: {mode}")
    print(f"  Model: {MODEL_PATH}")
    print("  URL: http://localhost:5001")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5001, debug=True, threaded=True)
