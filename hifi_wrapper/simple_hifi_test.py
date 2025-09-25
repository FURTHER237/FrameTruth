#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple HiFi test with error handling
"""

import sys
import os
import glob
from PIL import Image

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_single_image_simple(model, image_path):
    """Test a single image with simple output"""
    try:
        print(f"\nTesting: {os.path.basename(image_path)}")
        
        # Get image info
        with Image.open(image_path) as img:
            width, height = img.size
            print(f"  Image size: {width}x{height}")
        
        # Perform detection
        print("  Running detection...")
        result, probability = model.detect(image_path, verbose=False)
        
        if result is not None:
            status = "FORGED" if result == 1 else "REAL"
            print(f"  Result: {status} (confidence: {probability:.1%})")
            
            # Perform localization
            print("  Running localization...")
            mask = model.localize(image_path)
            
            if mask is not None:
                forgery_pixels = mask.sum()
                total_pixels = mask.size
                forgery_percentage = (forgery_pixels / total_pixels) * 100
                
                print(f"  Forgery regions: {'Yes' if forgery_pixels > 0 else 'No'}")
                if forgery_pixels > 0:
                    print(f"  Forgery coverage: {forgery_percentage:.1f}%")
                
                # Save mask
                output_dir = "simple_test_output"
                os.makedirs(output_dir, exist_ok=True)
                mask_filename = f"{os.path.splitext(os.path.basename(image_path))[0]}_mask.png"
                mask_path = os.path.join(output_dir, mask_filename)
                
                # Convert mask to PIL Image and save
                mask_img = Image.fromarray((mask * 255).astype('uint8'))
                mask_img.save(mask_path)
                print(f"  Mask saved: {mask_path}")
                
                return True
            else:
                print("  Localization failed")
                return False
        else:
            print("  Detection failed")
            return False
            
    except Exception as e:
        print(f"  Error: {e}")
        return False

def main():
    """Main test function"""
    print("HiFi Wrapper - Simple Test")
    print("=" * 40)
    
    try:
        print("Importing HiFi model...")
        from hifi_model import HiFiModel
        print("✓ Import successful")
        
        print("Initializing model...")
        model = HiFiModel(verbose=False)  # Less verbose
        print("✓ Model initialized")
        
        # Find images
        images_folder = "../images_to_test"
        if not os.path.exists(images_folder):
            print(f"❌ Images folder not found: {images_folder}")
            return False
        
        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png']:
            image_files.extend(glob.glob(os.path.join(images_folder, ext)))
            image_files.extend(glob.glob(os.path.join(images_folder, ext.upper())))
        
        if not image_files:
            print(f"❌ No images found")
            return False
        
        print(f"\nFound {len(image_files)} image(s)")
        
        # Test each image
        successful = 0
        for i, image_path in enumerate(image_files, 1):
            print(f"\n[{i}/{len(image_files)}]")
            if test_single_image_simple(model, image_path):
                successful += 1
        
        print(f"\n{'='*40}")
        print(f"Results: {successful}/{len(image_files)} successful")
        
        if successful > 0:
            print("✓ Some tests completed successfully!")
            print("Check 'simple_test_output' folder for generated masks")
        else:
            print("❌ All tests failed")
        
        return successful > 0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Test completed!")
    else:
        print("\n⚠️ Test failed!")
