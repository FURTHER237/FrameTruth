#!/usr/bin/env python3
"""
Simple test script for HiFi wrapper with images in the images_to_test folder
"""

import sys
import os
import glob
from PIL import Image

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_images():
    """Test all images in the images_to_test folder"""
    print("HiFi Wrapper - Simple Image Testing")
    print("=" * 50)
    
    try:
        from hifi_model import HiFiModel
        
        # Initialize the model
        print("Initializing HiFi Model...")
        model = HiFiModel(verbose=True)
        print("✓ Model ready!")
        
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
        for img in image_files:
            print(f"  - {os.path.basename(img)}")
        
        # Test each image
        results = []
        successful_tests = 0
        
        for i, image_path in enumerate(image_files, 1):
            print(f"\n[{i}/{len(image_files)}] Testing: {os.path.basename(image_path)}")
            
            try:
                # Get image info
                with Image.open(image_path) as img:
                    width, height = img.size
                    print(f"  Image size: {width}x{height}")
                
                # Perform detection
                print("  Performing detection...")
                result, probability = model.detect(image_path, verbose=False)
                
                if result is not None:
                    print(f"  Detection: {'🔴 FORGED' if result == 1 else '🟢 REAL'} (confidence: {probability:.1%})")
                    
                    # Perform localization
                    print("  Performing localization...")
                    mask = model.localize(image_path)
                    
                    if mask is not None:
                        forgery_pixels = mask.sum()
                        total_pixels = mask.size
                        forgery_percentage = (forgery_pixels / total_pixels) * 100
                        
                        print(f"  Forgery regions: {'Yes' if forgery_pixels > 0 else 'No'}")
                        if forgery_pixels > 0:
                            print(f"  Forgery coverage: {forgery_percentage:.1f}% of the image")
                            print(f"  Forgery pixels: {forgery_pixels:.0f} out of {total_pixels:,}")
                        
                        # Save mask
                        output_dir = "simple_test_output"
                        os.makedirs(output_dir, exist_ok=True)
                        mask_filename = f"{os.path.splitext(os.path.basename(image_path))[0]}_mask.png"
                        mask_path = os.path.join(output_dir, mask_filename)
                        
                        # Convert mask to PIL Image and save
                        mask_img = Image.fromarray((mask * 255).astype('uint8'))
                        mask_img.save(mask_path)
                        print(f"  Mask saved to: {mask_path}")
                        
                        results.append({
                            'image': os.path.basename(image_path),
                            'detection': result,
                            'probability': probability,
                            'forgery_pixels': forgery_pixels,
                            'forgery_percentage': forgery_percentage,
                            'mask_saved': mask_path
                        })
                        
                        successful_tests += 1
                    else:
                        print("  ❌ Localization failed!")
                else:
                    print("  ❌ Detection failed!")
                    
            except Exception as e:
                print(f"  ❌ Error testing image: {e}")
        
        # Summary
        print(f"\n{'='*50}")
        print("TESTING SUMMARY")
        print(f"{'='*50}")
        print(f"Total images: {len(image_files)}")
        print(f"Successful tests: {successful_tests}")
        print(f"Failed tests: {len(image_files) - successful_tests}")
        
        if results:
            print(f"\nDetailed Results:")
            for result in results:
                print(f"\n📁 {result['image']}:")
                print(f"   Detection: {'🔴 FORGED' if result['detection'] == 1 else '🟢 REAL'} ({result['probability']:.1%})")
                print(f"   Forgery: {'Yes' if result['forgery_pixels'] > 0 else 'No'}")
                if result['forgery_pixels'] > 0:
                    print(f"   Coverage: {result['forgery_percentage']:.1f}%")
                print(f"   Mask: {result['mask_saved']}")
        
        return successful_tests == len(image_files)
        
    except Exception as e:
        print(f"❌ Testing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_images()
    
    if success:
        print("\n🎉 All tests completed successfully!")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
