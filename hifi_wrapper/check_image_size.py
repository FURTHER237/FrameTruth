#!/usr/bin/env python3
"""
Script to check the original image dimensions
"""

import sys
import os
from PIL import Image

def check_image_size(image_path):
    """Check the dimensions of an image"""
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            print(f"Image: {os.path.basename(image_path)}")
            print(f"Original dimensions: {width} x {height}")
            print(f"Total pixels: {width * height:,}")
            return width, height
    except Exception as e:
        print(f"Error reading image: {e}")
        return None, None

def main():
    if len(sys.argv) != 2:
        print("Usage: python check_image_size.py <path_to_image>")
        return
    
    image_path = sys.argv[1]
    check_image_size(image_path)

if __name__ == "__main__":
    main()
