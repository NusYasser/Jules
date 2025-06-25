import pytesseract
from PIL import Image

def extract_text(image_path):
    """
    Extracts text from an image using Tesseract OCR.

    Args:
        image_path (str): The path to the image file.

    Returns:
        str: The extracted text, or None if an error occurred.
    """
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return text
    except FileNotFoundError:
        print(f"Error: File not found at {image_path}")
        return None
    except Exception as e:
        print(f"An error occurred during OCR: {e}")
        return None

if __name__ == '__main__':
    # Define the path to an existing screenshot file
    test_image_path = "screenshot_2025-05-29_13-23-45.png"

    # Call extract_text with the test image path
    extracted_text = extract_text(test_image_path)

    # Print the returned text
    if extracted_text is not None:
        print("Extracted Text:")
        print(extracted_text)
    else:
        print("No text could be extracted.")
