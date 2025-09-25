#!/usr/bin/env python3
"""
Test a single image to verify the detection logic
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hifi_model import HiFiModel

def test_single_image(image_path):
    """Test detection and analysis of a single image"""
    print(f"Testing image: {image_path}")
    print("=" * 50)
    
    # Initialize model
    model = HiFiModel(verbose=True)
    
    # Test detection only
    print("\n1. DETECTION TEST:")
    result, probability = model.detect(image_path, verbose=True)
    print(f"Raw result: {result}")
    print(f"Raw probability: {probability}")
    print(f"Is forged: {result == 1}")
    
    # Test analysis
    print("\n2. ANALYSIS TEST:")
    analysis = model.analyze_image(image_path, save_mask=False, save_confidence_mask=False, save_combined=False)
    
    print(f"Detection result: {analysis['detection']['result']}")
    print(f"Detection probability: {analysis['detection']['probability']}")
    print(f"Is forged: {analysis['detection']['is_forged']}")
    print(f"Has forgery (localization): {analysis['localization']['has_forgery']}")
    
    return analysis

if __name__ == "__main__":
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        image_path = "../images_to_test/5F7A5162.jpg"
    
    if not os.path.exists(image_path):
        print(f"Image not found: {image_path}")
        sys.exit(1)
    
    test_single_image(image_path)
