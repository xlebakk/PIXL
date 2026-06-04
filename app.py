import cv2
import re
import json
import base64
import numpy as np
import requests
from flask import Flask, request, jsonify, render_template, Response
from io import BytesIO

app = Flask(__name__)

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"

def ask_lm_studio(prompt):
    try:
        response = requests.post(LM_STUDIO_URL, json={
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        })
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"Ошибка LM Studio: {e}"

#  ВЕБ-КАМЕРА
def generate_frames():
    camera = cv2.VideoCapture(0)
    while True:
        success, frame = camera.read()
        if not success: break
        _, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

def parse_command(text: str) -> dict:
    t = text.lower().strip()
    if re.search(r"(повер|rotate|поворот)", t): return {"op": "rotate", "angle": _num(t, 90)}
    if re.search(r"(отраз|зеркал|flip)", t):
        direction = "vertical" if re.search(r"(верт|vert)", t) else "horizontal"
        return {"op": "flip", "direction": direction}
    if re.search(r"(размер|resize|масштаб|увелич.*размер)", t) or (re.search(r"уменьш", t) and not re.search(r"(яркост|контраст)", t)):
        m = re.search(r"(\d+)\s*[xXхХ]\s*(\d+)", t)
        if m: return {"op": "resize", "width": int(m.group(1)), "height": int(m.group(2))}
        n = _num(t)
        return {"op": "resize", "width": n or 800, "height": 0}
    if re.search(r"(чёрно|черно|серый|grayscale|обесцвет|ч/б)", t): return {"op": "grayscale"}
    if re.search(r"(канал|channel|оставь|только|выдел)", t):
        if re.search(r"(красн|red)", t):   return {"op": "channel", "keep": "red"}
        if re.search(r"(зелён|green)", t): return {"op": "channel", "keep": "green"}
        if re.search(r"(синий|blue)", t):  return {"op": "channel", "keep": "blue"}
    if re.search(r"(инверт|негатив|invert)", t): return {"op": "invert"}
    if re.search(r"(яркост|brightness)", t):
        n = _signed_num(t, 50)
        if re.search(r"(умен|убав|темн|сниз)", t) and n > 0: n = -n
        return {"op": "brightness", "value": n}
    if re.search(r"(контраст|contrast)", t):
        m2 = re.search(r"(\d+[.,]\d+)", t)
        alpha = float(m2.group(1).replace(",", ".")) if m2 else 1.5
        if re.search(r"(умен|убав|сниз)", t): alpha = 1 / alpha
        return {"op": "contrast", "alpha": alpha}
    if re.search(r"(разм|blur)", t):
        radius = _num(t, 5)
        if re.search(r"(гаусс|gaussian)", t): return {"op": "gaussian_blur", "radius": radius}
        return {"op": "blur", "radius": radius}
    if re.search(r"(сепи|sepia|старинн|ретро|vintage)", t): return {"op": "sepia"}
    if re.search(r"(кра[яе]|canny|контур|edge)", t): return {"op": "canny", "threshold1": _num(t, 100), "threshold2": _num(t, 100)*2}
    if re.search(r"(бинар|порог|threshold)", t): return {"op": "threshold", "value": _num(t, 127)}
    if re.search(r"(обреж|обрез|crop)", t):
        m2 = re.search(r"(\d+)\s*[xXхХ]\s*(\d+)", t)
        if m2: return {"op": "crop_center", "width": int(m2.group(1)), "height": int(m2.group(2))}
        n = _num(t, 200)
        return {"op": "crop_center", "width": n, "height": n}
    if re.search(r"(резк|sharpen|чёткост|четкост)", t): return {"op": "sharpen"}
    return {"op": "unknown", "message": f"Не распознана: «{text}»"}

def _num(text, default=0):
    m = re.search(r"\d+", text)
    return int(m.group()) if m else default

def _signed_num(text, default=0):
    m = re.search(r"[+-]?\d+", text)
    return int(m.group()) if m else default

#  ОПЕРАЦИИ OpenCV
def apply_op(img, parsed):
    op = parsed.get("op")
    if op == "rotate":
        angle = parsed.get("angle", 90)
        h, w = img.shape[:2]
        M = cv2.getRotationMatrix2D((w/2, h/2), -angle, 1.0)
        cos, sin = abs(M[0,0]), abs(M[0,1])
        nw, nh = int(h*sin+w*cos), int(h*cos+w*sin)
        M[0,2] += (nw-w)/2; M[1,2] += (nh-h)/2
        return cv2.warpAffine(img, M, (nw, nh))
    if op == "flip": return cv2.flip(img, 1 if parsed.get("direction") == "horizontal" else 0)
    if op == "resize":
        h, w = img.shape[:2]
        nw, nh = parsed.get("width", 0), parsed.get("height", 0)
        if nw == 0 and nh == 0: return img
        if nw == 0: nw = int(w * nh / h)
        if nh == 0: nh = int(h * nw / w)
        return cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LANCZOS4)
    if op == "grayscale": return cv2.cvtColor(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
    if op == "channel":
        result = np.zeros_like(img)
        idx = {"blue": 0, "green": 1, "red": 2}.get(parsed.get("keep", "red"), 2)
        result[:,:,idx] = img[:,:,idx]
        return result
    if op == "invert": return cv2.bitwise_not(img)
    if op == "brightness": return cv2.convertScaleAbs(img, alpha=1.0, beta=parsed.get("value", 50))
    if op == "contrast": return cv2.convertScaleAbs(img, alpha=parsed.get("alpha", 1.5), beta=0)
    if op == "blur":
        r = parsed.get("radius", 5)
        r = r if r % 2 == 1 else r + 1
        return cv2.blur(img, (r, r))
    if op == "gaussian_blur":
        r = parsed.get("radius", 5)
        r = r if r % 2 == 1 else r + 1
        return cv2.GaussianBlur(img, (r, r), 0)
    if op == "sepia":
        k = np.array([[0.272,0.534,0.131],[0.349,0.686,0.168],[0.393,0.769,0.189]])
        return np.clip(cv2.transform(img, k[:,::-1][::-1]), 0, 255).astype(np.uint8)
    if op == "crop_center":
        h, w = img.shape[:2]
        cw, ch = min(parsed.get("width",200), w), min(parsed.get("height",200), h)
        x, y = (w-cw)//2, (h-ch)//2
        return img[y:y+ch, x:x+cw]
    if op == "canny":
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, parsed.get("threshold1",100), parsed.get("threshold2",200))
        return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    if op == "threshold":
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, b = cv2.threshold(gray, parsed.get("value",127), 255, cv2.THRESH_BINARY)
        return cv2.cvtColor(b, cv2.COLOR_GRAY2BGR)
    if op == "sharpen":
        k = np.array([[0,-1,0],[-1,5,-1],[0,-1,0]], dtype=np.float32)
        return cv2.filter2D(img, -1, k)
    raise ValueError(f"Операция не найдена: {op}")

def img_to_base64(img):
    _, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 92])
    return base64.b64encode(buf).decode()

def base64_to_img(data):
    data = re.sub(r"^data:image/\w+;base64,", "", data)
    buf = np.frombuffer(base64.b64decode(data), dtype=np.uint8)
    return cv2.imdecode(buf, cv2.IMREAD_COLOR)

@app.route("/")
def index(): return render_template("index.html")

@app.route('/video_feed')
def video_feed(): return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/ai-chat', methods=['POST'])
def ai_chat(): return jsonify({"reply": ask_lm_studio(request.json.get("message"))})

@app.route("/apply", methods=["POST"])
def apply_route():
    data = request.get_json()
    cmd, img64 = data.get("command", ""), data.get("image", "")
    if not img64: return jsonify({"error": "Изображение отсутствует"}), 400
    img = base64_to_img(img64)
    parsed = parse_command(cmd)
    if parsed["op"] == "unknown": return jsonify({"error": parsed["message"], "parsed": parsed})
    try:
        result = apply_op(img, parsed)
        h, w = result.shape[:2]
        return jsonify({"image": "data:image/jpeg;base64," + img_to_base64(result), "op": parsed["op"]})
    except Exception as e: return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    import webbrowser, threading
    threading.Timer(1.0, lambda: webbrowser.open("http://localhost:5000")).start()
    app.run(debug=False, port=5000)