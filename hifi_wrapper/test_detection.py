#!/usr/bin/env python3
"""
Simple detection test to identify issues
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Starting detection test...")

try:
    from hifi_model import HiFiModel
    print("✅ Model import successful")
    
    model = HiFiModel(verbose=False)
    print("✅ Model initialization successful")
    
    # Test with available image
    test_image = "../images_to_test/DJI_0091-2.jpg"
    print(f"Testing with image: {test_image}")
    
    if os.path.exists(test_image):
        print("✅ Image exists")
        
        # Test detection
        result, prob = model.detect(test_image, verbose=True)
        print(f"Detection result: {result}, {prob}")
        
        if result is not None:
            print("✅ Detection successful")
        else:
            print("❌ Detection failed - result is None")
            
    else:
        print(f"❌ Image not found: {test_image}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
