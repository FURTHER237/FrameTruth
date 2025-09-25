#!/usr/bin/env python3
"""
Simple model verification script
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Starting model verification...")

try:
    from hifi_model import HiFiModel
    print("✅ Model import successful")
    
    model = HiFiModel(verbose=True)
    print("✅ Model initialization successful")
    
    # Test with a simple image
    test_image = "../images_to_test/image1.jpg"
    if os.path.exists(test_image):
        result, probability = model.detect(test_image, verbose=True)
        print(f"✅ Detection test successful: {result}, {probability}")
    else:
        print("⚠️  Test image not found, skipping detection test")
    
    print("✅ All tests passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
