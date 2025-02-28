import os
import xml.etree.ElementTree as ET
import cv2


def convert_xml_to_yolo(xml_file, out_file):
    """
    Converts a single XML annotation file to YOLO format.
    The XML is expected to be in VOC format and include an object with name "کل ناحیه پلاک".
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Try to get image size from the XML (if available)
    size = root.find('size')
    if size is not None:
        w = int(size.find('width').text)
        h = int(size.find('height').text)
    else:
        # If not in XML, read the image to get dimensions
        image_file = os.path.splitext(xml_file)[0] + '.jpg'
        img = cv2.imread(image_file)
        if img is None:
            print(f"Cannot read image for {xml_file}")
            return
        h, w = img.shape[:2]

    found = False
    for obj in root.findall('object'):
        name = obj.find('name').text.strip()
        if name == "کل ناحیه پلاک":
            found = True
            bndbox = obj.find('bndbox')
            xmin = float(bndbox.find('xmin').text)
            ymin = float(bndbox.find('ymin').text)
            xmax = float(bndbox.find('xmax').text)
            ymax = float(bndbox.find('ymax').text)
            # Convert to YOLO format (normalized center coordinates, width, height)
            x_center = ((xmin + xmax) / 2) / w
            y_center = ((ymin + ymax) / 2) / h
            box_width = (xmax - xmin) / w
            box_height = (ymax - ymin) / h
            # Since we have only one class ("plate"), class id = 0
            line = f"0 {x_center:.6f} {y_center:.6f} {box_width:.6f} {box_height:.6f}"
            with open(out_file, 'w') as f:
                f.write(line)
            break
    if not found:
        print(f"Warning: No plate bounding box found in {xml_file}")


if __name__ == '__main__':
    # Example for training set conversion:
    xml_dir = './test'
    label_dir = 'dataset/images/train'
    os.makedirs(label_dir, exist_ok=True)
    for filename in os.listdir(xml_dir):
        if filename.lower().endswith('.xml'):
            xml_path = os.path.join(xml_dir, filename)
            base = os.path.splitext(filename)[0]
            out_file = os.path.join(label_dir, base + '.txt')
            convert_xml_to_yolo(xml_path, out_file)

    # Example for training set conversion:
    xml_dir = './validation'
    label_dir = 'dataset/images/val'
    os.makedirs(label_dir, exist_ok=True)
    for filename in os.listdir(xml_dir):
        if filename.lower().endswith('.xml'):
            xml_path = os.path.join(xml_dir, filename)
            base = os.path.splitext(filename)[0]
            out_file = os.path.join(label_dir, base + '.txt')
            convert_xml_to_yolo(xml_path, out_file)

