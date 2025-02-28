import os
import glob
import cv2
from ultralytics import YOLO
import numpy as np
from PIL import Image, ImageFont, ImageDraw
import arabic_reshaper
from bidi.algorithm import get_display

# -----------------------------
# Load Models
# -----------------------------
# Replace with the correct paths to your model weights.
plate_detector = YOLO("./yolo12_detection_best.pt")  # Detection model
plate_reader = YOLO("./yolo12_recognition_best.pt")  # Recognition model

# -----------------------------
# Character Mapping (Reversed)
# -----------------------------
# Provided mapping from training (char -> int)
char_to_idx = {
    '۰': 0, '۱': 1, '۲': 2, '۳': 3, '۴': 4, '۵': 5, '۶': 6, '۷': 7, '۸': 8, '۹': 9,
    'D': 10, 'S': 11, 'الف': 12, 'ب': 13, 'ت': 14, 'تشریفات': 15, 'ث': 16, 'ج': 17,
    'د': 18, 'ز': 19, 'س': 20, 'ش': 21, 'ص': 22, 'ط': 23, 'ظ': 24, 'ع': 25, 'ف': 26,
    'ق': 27, 'ل': 28, 'م': 29, 'ن': 30, 'ه': 31, 'ه\u200d': 32, 'و': 33, 'پ': 34,
    'ژ (معلولین و جانبازان)': 35, 'ک': 36, 'گ': 37, 'ی': 38
}
# Reverse the mapping to get index -> character
idx_to_char = {v: k for k, v in char_to_idx.items()}


# -----------------------------
# Recognition Helper Function
# -----------------------------
def extract_plate_text(read_results):
    """
    Extracts predicted text from the recognition model's output.
    Sorts bounding boxes by x-coordinate. If sort_right_to_left=True,
    we sort descending so the rightmost character is first.
    """
    if not read_results:
        return ""

    result = read_results[0]
    try:
        boxes = result.boxes.xyxy.cpu().numpy()  # shape: (N,4)
        classes = result.boxes.cls.cpu().numpy()  # shape: (N,)
    except Exception as e:
        print("Error processing recognition output:", e)
        return ""

    # Collect (x1, class) pairs
    detections = []
    for box, cls in zip(boxes, classes):
        x1 = int(box[0])
        detections.append((x1, int(cls)))

    # If your plate is physically right-to-left in the image, use descending sort
    # If it's left-to-right, set sort_right_to_left=False
    detections.sort(key=lambda x: x[0])

    # Build the raw text from bounding boxes
    plate_text = "".join(idx_to_char.get(cls, "") for _, cls in detections)
    return plate_text


def draw_fancy_box(image_pil, box_coords, text, font,
                   # Set a more stylish color scheme:
                   fill_box=(30, 144, 255, 70),  # DodgerBlue with transparency
                   outline=(30, 144, 255, 255),  # Solid DodgerBlue
                   outline_width=3,
                   text_color=(255, 215, 0, 255)):  # Gold text color
    x1, y1, x2, y2 = box_coords

    # Create an RGBA overlay for the bounding box
    overlay = Image.new("RGBA", image_pil.size, (255, 255, 255, 0))
    overlay_draw = ImageDraw.Draw(overlay, "RGBA")
    overlay_draw.rectangle([x1, y1, x2, y2], fill=fill_box, outline=outline, width=outline_width)
    image_pil.alpha_composite(overlay)

    # Create an overlay for the text background
    overlay_text = Image.new("RGBA", image_pil.size, (255, 255, 255, 0))
    overlay_text_draw = ImageDraw.Draw(overlay_text, "RGBA")
    # Get text size using font.font.getsize
    text_size = font.font.getsize(text)
    # Check if the elements are tuples; if so, extract their first element
    if isinstance(text_size[0], tuple):
        text_width = int(text_size[0][0])
        text_height = int(text_size[1][0])
    else:
        text_width, text_height = int(text_size[0]), int(text_size[1])
    pad = 50
    tx1 = x1
    ty1 = max(y1 - text_height - 2 * pad, 0)
    image_pil.alpha_composite(overlay_text)

    # Draw the text on the main image
    draw_main = ImageDraw.Draw(image_pil)
    draw_main.text((tx1 + pad, ty1 + pad), text, font=font, fill=text_color)

# -----------------------------
# Main Processing Function
# -----------------------------
def process_image(image_path, font_size):
    """
    Processes a single image:
      1. Runs the plate detection model on the entire image.
      2. For each detected plate region, crops the region and runs the plate recognition model.
      3. Annotates the original image with bounding boxes and the recognized plate text.

    Returns the combined recognized text (if multiple boxes) and the annotated image.
    """
    # Load image using cv2 (BGR)
    image_cv = cv2.imread(image_path)
    if image_cv is None:
        print("Error: Could not read", image_path)
        return "", None

    # Create a copy for cropping (for recognition)
    image_copy = image_cv.copy()
    # Convert cv2 image (BGR) to PIL Image (RGB)
    image_pil = Image.fromarray(cv2.cvtColor(image_cv, cv2.COLOR_BGR2RGB)).convert("RGBA")
    draw = ImageDraw.Draw(image_pil)

    # Run detection on the original image
    detection_results = plate_detector(image_cv)
    predicted_texts = []

    # Load the desired Arabic font
    try:
        font = ImageFont.truetype("../app/fonts/Vazir-Bold.ttf", font_size)
    except IOError:
        print("Could not load the specified font. Using default font.")
        font = ImageFont.load_default()

    # For every detected plate region
    for detection in detection_results:
        for box in detection.boxes.xyxy.cpu().numpy().astype(int):
            x1, y1, x2, y2 = box
            # Crop the detected plate region from the cv2 copy for recognition
            crop = image_copy[y1:y2, x1:x2]
            read_results = plate_reader(crop)
            pred_text = extract_plate_text(read_results)
            predicted_texts.append(pred_text)

            # Process the text for proper Arabic display
            reshaped_text = arabic_reshaper.reshape(pred_text)
            # bidi_text = get_display(reshaped_text)

            # Draw the text above the bounding box using PIL
            # text_position = (x1, max(y1 - font_size - 10, 0))
            # draw.text(text_position, reshaped_text, font=font, fill=(0, 255, 0))
            draw_fancy_box(image_pil, (x1, y1, x2, y2), reshaped_text, font=font)

    combined_text = " ".join(predicted_texts)
    # Convert the annotated PIL image back to a cv2 image (BGR) for saving
    annotated_cv = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)
    return combined_text, annotated_cv


# -----------------------------
# Run Over Directory
# -----------------------------
def run_on_directory(test_dir, output_dir="recognized"):
    """
    Iterates through all JPG images in the test directory, runs the detection
    and recognition pipeline, and saves annotated images to the output directory.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    image_files = glob.glob(os.path.join(test_dir, "*.png"))
    for image_path in image_files:
        filename = os.path.basename(image_path)
        pred_text, annotated_img = process_image(image_path, 30)
        if annotated_img is not None:
            output_path = os.path.join(output_dir, filename)
            cv2.imwrite(output_path, annotated_img)
            print(f"{filename}: {pred_text}")


if __name__ == "__main__":
    test_dir = "./final_test"  # Directory with the 30 test images
    run_on_directory(test_dir, output_dir="./final_test_recognized")
