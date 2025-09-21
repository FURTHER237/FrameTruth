# rgb_to_grayscale.py
from PIL import Image
import os

def convert_image(input_path, output_path):
    """Convert an RGB image to grayscale and save it."""
    img = Image.open(input_path).convert("L")
    img.save(output_path)
    return output_path
