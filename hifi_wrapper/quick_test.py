#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick test to verify images and basic functionality
"""

import sys
import os
import glob
from PIL import Image

def test_images_basic():
    """Test basic image loading and properties"""
    print("HiFi Wrapper - Quick Image Test")
    print("=" * 50)
    
    # Find all images in the images_to_test folder
    images_folder = "../images_to_test"
    if not os.path.exists(images_folder):
        print(f"❌ Images folder not found: {images_folder}")
        return False
    
    # Get all image files
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff', '*.webp']
    image_files = []
    for ext in image_extensions:
        image_files.extend(glob.glob(os.path.join(images_folder, ext)))
        image_files.extend(glob.glob(os.path.join(images_folder, ext.upper())))
    
    if not image_files:
        print(f"❌ No images found in {images_folder}")
        return False
    
    print(f"\nFound {len(image_files)} image(s) to test:")
    
    # Test each image
    for i, image_path in enumerate(image_files, 1):
        print(f"\n[{i}/{len(image_files)}] Testing: {os.path.basename(image_path)}")
        
        try:
            # Get image info
            with Image.open(image_path) as img:
                width, height = img.size
                format_name = img.format
                mode = img.mode
                total_pixels = width * height
                
                print(f"  ✓ Image loaded successfully")
                print(f"  Dimensions: {width}x{height}")
                print(f"  Format: {format_name}")
                print(f"  Mode: {mode}")
                print(f"  Total pixels: {total_pixels:,}")
                
                # Check if image is suitable for processing
                if width < 64 or height < 64:
                    print(f"  ⚠️  Warning: Image is very small, may not work well with the model")
                elif width > 2048 or height > 2048:
                    print(f"  ⚠️  Warning: Image is very large, may be slow to process")
                else:
                    print(f"  ✓ Image size is suitable for processing")
                
        except Exception as e:
            print(f"  ❌ Error loading image: {e}")
            return False
    
    print(f"\n{'='*50}")
    print("BASIC TEST SUMMARY")
    print(f"{'='*50}")
    print(f"Total images: {len(image_files)}")
    print(f"All images loaded successfully: ✓")
    print(f"Images are ready for HiFi analysis!")
    
    return True

if __name__ == "__main__":
    success = test_images_basic()
    
    if success:
        print("\n🎉 Basic image tests passed!")
        print("Images are ready for HiFi forgery detection analysis.")
    else:
        print("\n⚠️  Basic image tests failed.")
