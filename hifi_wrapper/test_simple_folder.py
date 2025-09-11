#!/usr/bin/env python3
"""
Simple script to test all images in a designated folder
Just edit the FOLDER_PATH variable below and run the script
"""

import sys
import os
import glob

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# =============================================================================
# CONFIGURATION - Edit these variables as needed
# =============================================================================

# Path to the folder containing images to test
FOLDER_PATH = "../images_to_test"  # Change this to your desired folder

# Output directory for results
OUTPUT_DIR = "simple_test_output"  # Change this if you want a different output folder

# Whether to show detailed output
VERBOSE = True

# =============================================================================

def test_folder():
    """Test all images in the configured folder"""
    print("HiFi Wrapper - Simple Folder Testing")
    print("=" * 60)
    print(f"Testing folder: {FOLDER_PATH}")
    print(f"Output directory: {OUTPUT_DIR}")
    print("=" * 60)
    
    try:
        from hifi_model import HiFiModel
        
        # Check if folder exists
        if not os.path.exists(FOLDER_PATH):
            print(f"❌ Folder not found: {FOLDER_PATH}")
            print("Please edit the FOLDER_PATH variable in this script.")
            return False
        
        # Initialize the model
        if VERBOSE:
            print("Initializing HiFi Model...")
        model = HiFiModel(verbose=False)
        if VERBOSE:
            print("✓ Model ready!")
        
        # Get all image files
        image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff', '*.webp']
        image_files = []
        for ext in image_extensions:
            image_files.extend(glob.glob(os.path.join(FOLDER_PATH, ext)))
            image_files.extend(glob.glob(os.path.join(FOLDER_PATH, ext.upper())))
        
        # Remove duplicates and sort
        image_files = sorted(list(set(image_files)))
        
        if not image_files:
            print(f"❌ No images found in {FOLDER_PATH}")
            print("Supported formats: JPG, JPEG, PNG, BMP, TIFF, WEBP")
            return False
        
        if VERBOSE:
            print(f"\nFound {len(image_files)} image(s) to test:")
            for img in image_files:
                print(f"  - {os.path.basename(img)}")
        
        # Test each image
        successful_tests = 0
        failed_tests = 0
        forged_count = 0
        real_count = 0
        
        for i, image_path in enumerate(image_files, 1):
            if VERBOSE:
                print(f"\n[{i}/{len(image_files)}] Processing {os.path.basename(image_path)}...")
            
            try:
                # Perform enhanced analysis
                results = model.analyze_image(
                    image_path, 
                    save_mask=True, 
                    output_dir=OUTPUT_DIR,
                    save_confidence_mask=True,
                    save_combined=True
                )
                
                if results and results['localization']['mask'] is not None:
                    detection = results['detection']
                    localization = results['localization']
                    
                    if VERBOSE:
                        if detection['result'] is not None:
                            status = '🔴 FORGED' if detection['is_forged'] else '🟢 REAL'
                            confidence = f"({detection['probability']:.1%})"
                            print(f"  ✓ Detection: {status} {confidence}")
                            
                            if detection['is_forged']:
                                forged_count += 1
                            else:
                                real_count += 1
                        else:
                            print(f"  ⚠ Detection: FAILED")
                        
                        print(f"  ✓ Forgery: {'Yes' if localization['has_forgery'] else 'No'}")
                        
                        if localization['has_forgery'] and localization['mask'] is not None:
                            mask = localization['mask']
                            forgery_pixels = mask.sum()
                            total_pixels = mask.size
                            forgery_percentage = (forgery_pixels / total_pixels) * 100
                            print(f"  ✓ Coverage: {forgery_percentage:.1f}%")
                        
                        print(f"  ✓ Mask Size: {localization['mask_size']}")
                    
                    successful_tests += 1
                else:
                    if VERBOSE:
                        print(f"  ❌ Analysis failed")
                    failed_tests += 1
                    
            except Exception as e:
                if VERBOSE:
                    print(f"  ❌ Error: {e}")
                failed_tests += 1
        
        # Summary
        print(f"\n{'='*60}")
        print("SIMPLE FOLDER TESTING SUMMARY")
        print(f"{'='*60}")
        print(f"Folder: {FOLDER_PATH}")
        print(f"Total images: {len(image_files)}")
        print(f"Successful tests: {successful_tests}")
        print(f"Failed tests: {failed_tests}")
        
        if successful_tests > 0:
            print(f"\nDetection Results:")
            print(f"  🔴 Forged: {forged_count}")
            print(f"  🟢 Real: {real_count}")
        
        print(f"\nOutput Files Created in '{OUTPUT_DIR}/':")
        print(f"  📁 Binary Masks: *_mask.png")
        print(f"  🎨 Confidence Masks: *_confidence_mask.png")
        print(f"  🖼️  Combined Images: *_combined.png")
        
        if successful_tests == len(image_files):
            print(f"\n🎉 All tests completed successfully!")
        else:
            print(f"\n⚠️  {failed_tests} test(s) failed.")
        
        return successful_tests > 0
        
    except Exception as e:
        print(f"❌ Testing failed: {e}")
        if VERBOSE:
            import traceback
            traceback.print_exc()
        return False

def main():
    """Main function"""
    print("To test a different folder, edit the FOLDER_PATH variable in this script.")
    print("Current configuration:")
    print(f"  FOLDER_PATH = '{FOLDER_PATH}'")
    print(f"  OUTPUT_DIR = '{OUTPUT_DIR}'")
    print(f"  VERBOSE = {VERBOSE}")
    print()
    
    success = test_folder()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
