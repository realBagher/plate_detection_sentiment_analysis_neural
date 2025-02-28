import os
import glob
import csv
import xml.etree.ElementTree as ET


def get_box_coords(obj):
    """
    Given an XML <object> element, return its bounding box as a tuple of integers: (xmin, ymin, xmax, ymax)
    """
    bndbox = obj.find("bndbox")
    xmin = float(bndbox.find("xmin").text)
    ymin = float(bndbox.find("ymin").text)
    xmax = float(bndbox.find("xmax").text)
    ymax = float(bndbox.find("ymax").text)
    return xmin, ymin, xmax, ymax


def is_inside(child_box, parent_box, tolerance=0):
    """
    Check if the child_box is inside the parent_box.
    Optionally, a tolerance can be provided.
    """
    cxmin, cymin, cxmax, cymax = child_box
    pxmin, pymin, pxmax, pymax = parent_box
    return (cxmin >= pxmin - tolerance and cymin >= pymin - tolerance and
            cxmax <= pxmax + tolerance and cymax <= pymax + tolerance)


def get_image_filename(xml_file):
    """
    Given an xml_file path and the extracted filename from <filename>,
    determine the full path to the corresponding image.
    Uses the XML file's directory as the base.
    """
    base_dir = os.path.dirname(xml_file)  # use the XML file’s directory

    candidate = str.split(str.split(xml_file, "/")[-1], ".")[0] + ".jpg"

    return candidate

def extract_plate_labels_from_xml(xml_file):
    """
    Parses an XML file and extracts the plate label(s) based on the annotations.
    It groups annotations by plate regions marked with "کل ناحیه پلاک" and
    collects the characters (all objects whose name is not "کل ناحیه پلاک")
    that fall inside each plate region.

    Returns a list of tuples: (filename, plate_label)
    """
    try:
        tree = ET.parse(xml_file)
    except Exception as e:
        print(f"Error parsing {xml_file}: {e}")
        return []

    root = tree.getroot()

    image_filename = get_image_filename(xml_file)

    # Collect all object elements
    objects = root.findall("object")

    # Identify plate region objects (with name "کل ناحیه پلاک")
    plate_regions = []
    for obj in objects:
        name = obj.find("name").text.strip()
        if name == "کل ناحیه پلاک":
            box = get_box_coords(obj)
            plate_regions.append(box)

    if not plate_regions:
        # If no plate region is marked, we can optionally use all objects.
        print(f"No plate region ('کل ناحیه پلاک') found in {xml_file}.")
        return []

    # For each plate region, find the character objects within it.
    plate_labels = []
    for region in plate_regions:
        char_objs = []
        for obj in objects:
            name = obj.find("name").text.strip()
            # Skip the full plate region object itself
            if name == "کل ناحیه پلاک":
                continue
            # Check if the object's bounding box is inside the current plate region.
            box = get_box_coords(obj)
            if is_inside(box, region, tolerance=0):
                # Save tuple of (xmin, character)
                char_objs.append((box[0], name))

        if char_objs:
            # Sort by xmin and join the characters
            char_objs.sort(key=lambda x: x[0])
            plate_text = "".join([char for _, char in char_objs])
            plate_labels.append((image_filename, plate_text))

    return plate_labels


def find_xml_files_in_dirs(directories, pattern="*.xml"):
    """
    Given a list of directories, find all XML files within them (non-recursively).
    """
    xml_files = []
    for directory in directories:
        dir_path = os.path.abspath(directory)
        found = glob.glob(os.path.join(dir_path, pattern))
        xml_files.extend(found)
    return xml_files


def main():
    # Directories where your testset objects are located (with associated XML files)
    directories = ["./test", "./validation"]

    # Find XML files in these directories
    xml_files = find_xml_files_in_dirs(directories)
    print(f"Found {len(xml_files)} XML files in {directories}.")

    # Process each XML file to extract plate labels.
    results = []  # List of (filename, plate_label)
    for xml_file in xml_files:
        labels = extract_plate_labels_from_xml(xml_file)
        if labels:
            results.extend(labels)

    if not results:
        print("No plate labels extracted.")
        return

    # Save results to a CSV file
    output_csv = "extracted_plate_labels.csv"
    with open(output_csv, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["image_filename", "plate_label"])
        for image_filename, plate_label in results:
            writer.writerow([image_filename, plate_label])

    print(f"Extracted plate labels have been saved to {output_csv}.")


if __name__ == "__main__":
    main()
