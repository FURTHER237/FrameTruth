#!/usr/bin/env python3
"""
Test all images with enhanced mask features
"""

import sys
import os
import glob

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_all_enhanced():
    """Test all images with enhanced mask features"""
    print("HiFi Wrapper - Enhanced Mask Batch Testing")
    print("=" * 60)
    
    try:
        from hifi_model import HiFiModel
        
        # Initialize the model
        print("Initializing HiFi Model...")
        model = HiFiModel(verbose=False)
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
        
        # Remove duplicates
        image_files = list(set(image_files))
        
        if not image_files:
            print(f"❌ No images found in {images_folder}")
            return False
        
        print(f"\nFound {len(image_files)} image(s) to test:")
        for img in image_files:
            print(f"  - {os.path.basename(img)}")
        
        # Test each image
        successful_tests = 0
        
        for i, image_path in enumerate(image_files, 1):
            print(f"\n[{i}/{len(image_files)}] Processing {os.path.basename(image_path)}...")
            
            try:
                # Perform enhanced analysis
                results = model.analyze_image(
                    image_path, 
                    save_mask=True, 
                    output_dir="batch_enhanced_output",
                    save_confidence_mask=True,
                    save_combined=True
                )
                
                if results and results['localization']['mask'] is not None:
                    detection = results['detection']
                    localization = results['localization']
                    
                    print(f"  ✓ Detection: {'🔴 FORGED' if detection['is_forged'] else '🟢 REAL'} ({detection['probability']:.1%})")
                    print(f"  ✓ Forgery: {'Yes' if localization['has_forgery'] else 'No'}")
                    
                    if localization['has_forgery']:
                        mask = localization['mask']
                        forgery_pixels = mask.sum()
                        total_pixels = mask.size
                        forgery_percentage = (forgery_pixels / total_pixels) * 100
                        print(f"  ✓ Coverage: {forgery_percentage:.1f}%")
                    
                    print(f"  ✓ Mask Size: {localization['mask_size']}")
                    successful_tests += 1
                else:
                    print(f"  ❌ Analysis failed")
                    
            except Exception as e:
                print(f"  ❌ Error: {e}")
        
        # Summary
        print(f"\n{'='*60}")
        print("ENHANCED BATCH TESTING SUMMARY")
        print(f"{'='*60}")
        print(f"Total images: {len(image_files)}")
        print(f"Successful tests: {successful_tests}")
        print(f"Failed tests: {len(image_files) - successful_tests}")
        
        print(f"\nOutput Files Created in 'batch_enhanced_output/':")
        print(f"  📁 Binary Masks: *_mask.png")
        print(f"  🎨 Confidence Masks: *_confidence_mask.png")
        print(f"  🖼️  Combined Images: *_combined.png")
        
        print(f"\nMask Types:")
        print(f"  • Binary Mask: Black/white showing forgery regions")
        print(f"  • Confidence Mask: Red intensity = confidence level")
        print(f"  • Combined Image: Original + red overlay")
        
        return successful_tests == len(image_files)
        
    except Exception as e:
        print(f"❌ Batch testing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    success = test_all_enhanced()
    
    if success:
        print("\n🎉 All enhanced tests completed successfully!")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
