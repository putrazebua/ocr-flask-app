
from flask import Flask, render_template, request, url_for, jsonify
import cv2, numpy as np, io, base64, os, uuid
from PIL import Image
import pytesseract

app = Flask(__name__)
app.secret_key = 'rahasia_aman_123'
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def process_image_and_ocr(image_stream, threshold_value):
    file_bytes = np.frombuffer(image_stream.read(), np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    actual_threshold = int(threshold_value / 100 * 255)
    _, thresh = cv2.threshold(gray, actual_threshold, 255, cv2.THRESH_BINARY)
    pil_img = Image.fromarray(thresh)
    filename = f"{uuid.uuid4().hex}.png"
    filepath = os.path.join('static', filename)
    pil_img.save(filepath)
    buffer = io.BytesIO()
    pil_img.save(buffer, format="PNG")
    encoded_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
    config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    ocr_result = pytesseract.image_to_string(pil_img, config=config).strip()
    return encoded_image, ocr_result, filename

@app.route('/', methods=['GET'])
def index():
    return render_template("index.html")

@app.route('/process', methods=['POST'])
def process():
    file = request.files.get('image')
    if not file or file.filename == '':
        return render_template("index.html", ocr_result="Gagal: tidak ada file.")
    threshold_value = float(request.form.get('threshold', 50))
    file.stream.seek(0)
    processed_image, ocr_result, filename = process_image_and_ocr(file, threshold_value)
    return render_template("index.html",
        processed_image=processed_image,
        ocr_result=ocr_result,
        download_link=url_for('static', filename=filename),
        threshold_value=threshold_value
    )

@app.route('/update_threshold', methods=['POST'])
def update_threshold():
    file = request.files.get('image')
    threshold_value = float(request.form.get('threshold', 50))
    file.stream.seek(0)
    processed_image, _, _ = process_image_and_ocr(file, threshold_value)
    return jsonify({ "processed_image": processed_image })

@app.route('/help')
def help_page():
    return render_template("help.html")





if __name__ == "__main__":
    os.makedirs("static", exist_ok=True)
    port = int(os.environ.get("PORT", 5000))  # port disediakan oleh Render
    app.run(debug=False, host="0.0.0.0", port=port)
