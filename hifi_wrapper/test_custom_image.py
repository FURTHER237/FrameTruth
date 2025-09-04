#!/usr/bin/env python3
"""
Test script for HiFi wrapper with custom image from images_to_test folder
"""

import sys
import os

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_custom_image():
    """Test the wrapper with the custom image"""
    print("=" * 60)
    print("Testing HiFi Wrapper with Custom Image")
    print("=" * 60)
    
    try:
        from hifi_model import HiFiModel
        
        # Initialize the model
        print("Initializing HiFi Model...")
        model = HiFiModel(verbose=True)
        print("✓ Model initialized successfully!")
        
        # Test image path
        test_image_path = "../images_to_test/image1.jpg"
        
        if not os.path.exists(test_image_path):
            print(f"✗ Test image not found: {test_image_path}")
            return False
        
        print(f"\nTesting with image: {test_image_path}")
        
        # Test detection
        print("\n" + "-" * 40)
        print("Testing Image Detection")
        print("-" * 40)
        result, probability = model.detect(test_image_path, verbose=True)
        
        if result is not None:
            print("✓ Detection successful!")
            print(f"Result: {'Forged' if result == 1 else 'Real'}")
            print(f"Probability: {probability:.3f}")
        else:
            print("✗ Detection failed!")
            return False
        
        # Test localization
        print("\n" + "-" * 40)
        print("Testing Image Localization")
        print("-" * 40)
        mask = model.localize(test_image_path)
        
        if mask is not None:
            print("✓ Localization successful!")
            print(f"Mask shape: {mask.shape}")
            forgery_pixels = mask.sum()
            total_pixels = mask.size
            forgery_percentage = (forgery_pixels / total_pixels) * 100
            print(f"Forgery pixels: {forgery_pixels:.0f}")
            print(f"Forgery coverage: {forgery_percentage:.2f}% of the image")
        else:
            print("✗ Localization failed!")
            return False
        
        # Test complete analysis
        print("\n" + "-" * 40)
        print("Testing Complete Analysis")
        print("-" * 40)
        results = model.analyze_image(test_image_path, save_mask=True, output_dir="custom_output")
        
        print("✓ Complete analysis successful!")
        print(f"\nFinal Results:")
        print(f"  Detection: {'Forged' if results['detection']['is_forged'] else 'Real'}")
        print(f"  Confidence: {results['detection']['probability']:.3f}")
        print(f"  Has Forgery Regions: {results['localization']['has_forgery']}")
        
        if results['localization']['mask'] is not None:
            mask = results['localization']['mask']
            forgery_pixels = mask.sum()
            total_pixels = mask.size
            forgery_percentage = (forgery_pixels / total_pixels) * 100
            print(f"  Forgery Coverage: {forgery_percentage:.2f}% of the image")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("HiFi Wrapper Test with Custom Image")
    print("=" * 60)
    
    success = test_custom_image()
    
    if success:
        print("\n🎉 Test completed successfully!")
        print("Check the 'custom_output' folder for the saved localization mask.")
    else:
        print("\n❌ Test failed!")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
