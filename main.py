import cv2
from PIL import ImageFont, ImageDraw, Image, ImageTk
from easyocr import Reader
from tkinter import Tk, Label, filedialog, Toplevel
import numpy as np
import os
import re

# Sử dụng tkinter để mở hộp thoại chọn file
root = Tk()
root.withdraw()  # Ẩn cửa sổ gốc của tkinter
filetypes = [("Image files", "*.jpg *.jpeg *.png *.webp"), ("Video files", "*.mp4 *.avi *.mov *.mkv")]
filenames = filedialog.askopenfilenames(title="Chọn ảnh hoặc video", filetypes=filetypes)

if not filenames:
    raise FileNotFoundError("Không có file nào được chọn.")

# Tải font chữ
fontpath = r"C:\Users\tiphu\Downloads\Compressed\arial.ttf-master\arial.ttf-master\arial.ttf"
font = ImageFont.truetype(fontpath, 40)

# Định nghĩa màu chữ (RGB và alpha)
b, g, r, a = 0, 255, 0, 0

# Khởi tạo đối tượng EasyOCR reader
reader = Reader(['en'])

# Hàm lọc bỏ ký tự đặc biệt, chỉ giữ lại chữ và số
def filter_text(text):
    return re.sub(r'[^A-Za-z0-9]', '', text)

# Hàm xử lý và hiển thị kết quả cho một khung hình
def process_frame(frame, correct_plate):
    img = cv2.resize(frame, (800, 600))

    # Chuyển ảnh sang ảnh xám
    grayscale = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(grayscale, (5, 5), 0)

    edged = cv2.Canny(blurred, 10, 200)
    contours, _ = cv2.findContours(edged, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

    number_plate_shape = None
    for c in contours:
        perimeter = cv2.arcLength(c, True)
        approximation = cv2.approxPolyDP(c, 0.02 * perimeter, True)
        if len(approximation) == 4:  # Hình chữ nhật
            number_plate_shape = approximation
            break

    text = "Không tìm thấy biển số xe"
    is_correct = "Sai"
    if number_plate_shape is not None:
        x, y, w, h = cv2.boundingRect(number_plate_shape)
        number_plate = grayscale[y:y + h, x:x + w]
        detection = reader.readtext(number_plate)
        if len(detection) != 0:
            detected_plate = filter_text(detection[0][1])
            text = f"Biển số: {detection[0][1]}"
            if detected_plate == correct_plate:
                is_correct = "Đúng"
            else:
                is_correct = "Sai"
            # Vẽ khung xung quanh biển số
            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
    return img, text, is_correct

# Hiển thị kết quả video
def show_video(filename, correct_plate):
    # Mở video
    cap = cv2.VideoCapture(filename)
    if not cap.isOpened():
        raise FileNotFoundError("Không thể mở file video được chọn.")

    # Tạo cửa sổ hiển thị kết quả
    result_window = Toplevel(root)
    result_window.title(f"Kết quả nhận diện biển số xe - {os.path.basename(filename)}")

    # Nhãn để hiển thị ảnh
    img_label = Label(result_window)
    img_label.pack(side="left")

    # Nhãn để hiển thị kết quả nhận diện
    result_label = Label(result_window, font=("Arial", 40))
    result_label.pack(side="right")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        processed_img, text, is_correct = process_frame(frame, correct_plate)

        # Resize ảnh để hiển thị nhỏ hơn
        display_img = cv2.resize(processed_img, (800, 600))

        # Hiển thị ảnh
        img_rgb = cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        img_tk = ImageTk.PhotoImage(img_pil)
        img_label.config(image=img_tk)
        img_label.image = img_tk  # Giữ tham chiếu để ảnh không bị xóa

        # Hiển thị kết quả nhận diện
        result_label.config(text=f"{text}\nKết quả: {is_correct}")

        result_window.update_idletasks()
        result_window.update()

    cap.release()
    cv2.destroyAllWindows()

# Hiển thị kết quả ảnh
def show_image(filename, correct_plate):
    img = cv2.imread(filename)
    if img is None:
        raise FileNotFoundError("Không thể đọc file ảnh được chọn.")

    processed_img, text, is_correct = process_frame(img, correct_plate)

    # Tạo cửa sổ hiển thị kết quả
    result_window = Toplevel(root)
    result_window.title(f"Kết quả nhận diện biển số xe - {os.path.basename(filename)}")

    # Resize ảnh để hiển thị nhỏ hơn
    display_img = cv2.resize(processed_img, (800, 400))

    # Hiển thị ảnh
    img_rgb = cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(img_rgb)
    img_tk = ImageTk.PhotoImage(img_pil)
    img_label = Label(result_window, image=img_tk)
    img_label.image = img_tk  # Giữ tham chiếu để ảnh không bị xóa
    img_label.pack(side="left")

    # Hiển thị kết quả nhận diện với font lớn hơn
    result_label = Label(result_window, text=f"{text}\nKết quả: {is_correct}", font=("Arial", 40))
    result_label.pack(side="right")
    result_window.mainloop()

# Lặp qua từng file và xử lý
for filename in filenames:
    correct_plate = filter_text(os.path.splitext(os.path.basename(filename))[0])
    ext = os.path.splitext(filename)[1].lower()
    if ext in ['.mp4', '.avi', '.mov', '.mkv']:
        show_video(filename, correct_plate)
    else:
        show_image(filename, correct_plate)
