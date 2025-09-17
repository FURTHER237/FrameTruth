#!/usr/bin/env python3
"""
Simple script to test a single image with detailed output
Usage: python test_image.py <path_to_image>
"""

import sys
import os
from PIL import Image

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def get_image_info(image_path):
    """Get detailed information about an image"""
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            format_name = img.format
            mode = img.mode
            file_size = os.path.getsize(image_path)
            
            return {
                'width': width,
                'height': height,
                'format': format_name,
                'mode': mode,
                'total_pixels': width * height,
                'file_size_mb': file_size / (1024 * 1024)
            }
    except Exception as e:
        return {'error': str(e)}

def test_image(image_path):
    """Test a single image with detailed output"""
    try:
        from hifi_model import HiFiModel
        
        print("HiFi Wrapper - Single Image Test")
        print("=" * 50)
        
        # Check if image exists
        if not os.path.exists(image_path):
            print(f"❌ Image not found: {image_path}")
            return False
        
        # Get image information
        print(f"Image: {os.path.basename(image_path)}")
        print(f"Path: {image_path}")
        
        img_info = get_image_info(image_path)
        if 'error' in img_info:
            print(f"❌ Error reading image: {img_info['error']}")
            return False
        
        print(f"\nImage Information:")
        print(f"  Dimensions: {img_info['width']} x {img_info['height']}")
        print(f"  Format: {img_info['format']}")
        print(f"  Color Mode: {img_info['mode']}")
        print(f"  Total Pixels: {img_info['total_pixels']:,}")
        print(f"  File Size: {img_info['file_size_mb']:.2f} MB")
        
        # Initialize model
        print(f"\nInitializing HiFi Model...")
        model = HiFiModel(verbose=False)
        print("✓ Model ready!")
        
        # Perform analysis
        print(f"\nPerforming analysis...")
        results = model.analyze_image(image_path, save_mask=True, output_dir="single_test_output")
        
        if results is None:
            print("❌ Analysis failed!")
            return False
        
        # Display results
        print(f"\n" + "=" * 50)
        print("ANALYSIS RESULTS")
        print("=" * 50)
        
        detection = results['detection']
        localization = results['localization']
        
        print(f"Detection Result:")
        print(f"  Status: {'🔴 FORGED' if detection['is_forged'] else '🟢 REAL'}")
        print(f"  Confidence: {detection['probability']:.1%}")
        print(f"  Raw Probability: {detection['probability']:.6f}")
        
        if localization['mask'] is not None:
            mask = localization['mask']
            forgery_pixels = mask.sum()
            total_pixels = mask.size
            forgery_percentage = (forgery_pixels / total_pixels) * 100
            
            print(f"\nLocalization Result:")
            print(f"  Forgery Regions: {'Yes' if localization['has_forgery'] else 'No'}")
            print(f"  Mask Size: {mask.shape}")
            print(f"  Forgery Coverage: {forgery_percentage:.2f}% of the image")
            print(f"  Forgery Pixels: {forgery_pixels:.0f} out of {total_pixels:,}")
            print(f"  Real Pixels: {total_pixels - forgery_pixels:.0f}")
        
        print(f"\nOutput Files:")
        print(f"  Localization mask: single_test_output/{os.path.splitext(os.path.basename(image_path))[0]}_mask.png")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python test_image.py <path_to_image>")
        print("\nExamples:")
        print("  python test_image.py ../images_to_test/image1.jpg")
        print("  python test_image.py ../images_to_test/1a-1.webp")
        return False
    
    image_path = sys.argv[1]
    return test_image(image_path)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
