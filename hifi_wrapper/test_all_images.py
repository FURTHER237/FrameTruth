#!/usr/bin/env python3
"""
Test script for HiFi wrapper with all images in the images_to_test folder
"""

import sys
import os
import glob
from PIL import Image

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def get_image_info(image_path):
    """Get basic information about an image"""
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            format_name = img.format
            mode = img.mode
            return {
                'width': width,
                'height': height,
                'format': format_name,
                'mode': mode,
                'total_pixels': width * height
            }
    except Exception as e:
        return {'error': str(e)}

def test_single_image(model, image_path, output_dir="batch_output"):
    """Test a single image"""
    try:
        print(f"\n{'='*60}")
        print(f"Testing: {os.path.basename(image_path)}")
        print(f"{'='*60}")
        
        # Get image info
        img_info = get_image_info(image_path)
        if 'error' in img_info:
            print(f"❌ Error reading image: {img_info['error']}")
            return None
        
        print(f"Image Info:")
        print(f"  Dimensions: {img_info['width']} x {img_info['height']}")
        print(f"  Format: {img_info['format']}")
        print(f"  Mode: {img_info['mode']}")
        print(f"  Total Pixels: {img_info['total_pixels']:,}")
        
        # Perform analysis
        print(f"\nPerforming analysis...")
        results = model.analyze_image(image_path, save_mask=True, output_dir=output_dir)
        
        if results is None:
            print("❌ Analysis failed!")
            return None
        
        # Display results
        detection = results['detection']
        localization = results['localization']
        
        print(f"\nResults:")
        print(f"  Detection: {'🔴 FORGED' if detection['is_forged'] else '🟢 REAL'}")
        print(f"  Confidence: {detection['probability']:.1%}")
        
        if localization['mask'] is not None:
            mask = localization['mask']
            forgery_pixels = mask.sum()
            total_pixels = mask.size
            forgery_percentage = (forgery_pixels / total_pixels) * 100
            
            print(f"  Forgery Regions: {'Yes' if localization['has_forgery'] else 'No'}")
            if localization['has_forgery']:
                print(f"  Forgery Coverage: {forgery_percentage:.1f}% of the image")
                print(f"  Forgery Pixels: {forgery_pixels:.0f} out of {total_pixels:,}")
            
            print(f"  Mask Size: {mask.shape}")
        
        # Save results summary
        result_summary = {
            'image': os.path.basename(image_path),
            'image_info': img_info,
            'detection': detection,
            'localization': {
                'has_forgery': localization['has_forgery'],
                'mask_size': localization['mask_size'],
                'forgery_coverage': (mask.sum() / mask.size * 100) if mask is not None else 0
            }
        }
        
        return result_summary
        
    except Exception as e:
        print(f"❌ Error testing image: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_all_images():
    """Test all images in the images_to_test folder"""
    print("HiFi Wrapper - Batch Image Testing")
    print("=" * 60)
    
    try:
        from hifi_model import HiFiModel
        
        # Initialize the model
        print("Initializing HiFi Model...")
        model = HiFiModel(verbose=False)  # Less verbose for batch processing
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
            print(f"\n[{i}/{len(image_files)}] Processing...")
            result = test_single_image(model, image_path)
            if result:
                results.append(result)
                successful_tests += 1
        
        # Summary
        print(f"\n{'='*60}")
        print("BATCH TESTING SUMMARY")
        print(f"{'='*60}")
        print(f"Total images: {len(image_files)}")
        print(f"Successful tests: {successful_tests}")
        print(f"Failed tests: {len(image_files) - successful_tests}")
        
        if results:
            print(f"\nDetailed Results:")
            for result in results:
                img_name = result['image']
                detection = result['detection']
                localization = result['localization']
                
                print(f"\n📁 {img_name}:")
                print(f"   Detection: {'🔴 FORGED' if detection['is_forged'] else '🟢 REAL'} ({detection['probability']:.1%})")
                print(f"   Forgery: {'Yes' if localization['has_forgery'] else 'No'}")
                if localization['has_forgery']:
                    print(f"   Coverage: {localization['forgery_coverage']:.1f}%")
                print(f"   Mask Size: {localization['mask_size']}")
        
        print(f"\n✓ All masks saved to: batch_output/")
        return successful_tests == len(image_files)
        
    except Exception as e:
        print(f"❌ Batch testing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    success = test_all_images()
    
    if success:
        print("\n🎉 All tests completed successfully!")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
