#!/usr/bin/env python3
"""
Test all images in a designated folder with enhanced mask features
"""

import sys
import os
import glob
import argparse

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_folder_images(folder_path, output_dir="folder_test_output", verbose=True):
    """
    Test all images in a designated folder
    
    Args:
        folder_path (str): Path to the folder containing images
        output_dir (str): Directory to save outputs
        verbose (bool): Whether to show detailed output
        
    Returns:
        dict: Test results summary
    """
    print("HiFi Wrapper - Folder Image Testing")
    print("=" * 60)
    
    try:
        from hifi_model import HiFiModel
        
        # Check if folder exists
        if not os.path.exists(folder_path):
            print(f"❌ Folder not found: {folder_path}")
            return {"success": False, "error": "Folder not found"}
        
        # Initialize the model
        if verbose:
            print("Initializing HiFi Model...")
        model = HiFiModel(verbose=False)
        if verbose:
            print("✓ Model ready!")
        
        # Get all image files
        image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff', '*.webp']
        image_files = []
        for ext in image_extensions:
            image_files.extend(glob.glob(os.path.join(folder_path, ext)))
            image_files.extend(glob.glob(os.path.join(folder_path, ext.upper())))
        
        # Remove duplicates and sort
        image_files = sorted(list(set(image_files)))
        
        if not image_files:
            print(f"❌ No images found in {folder_path}")
            return {"success": False, "error": "No images found"}
        
        if verbose:
            print(f"\nFound {len(image_files)} image(s) to test:")
            for img in image_files:
                print(f"  - {os.path.basename(img)}")
        
        # Test each image
        results = {
            "total_images": len(image_files),
            "successful_tests": 0,
            "failed_tests": 0,
            "detection_results": [],
            "localization_results": []
        }
        
        for i, image_path in enumerate(image_files, 1):
            if verbose:
                print(f"\n[{i}/{len(image_files)}] Processing {os.path.basename(image_path)}...")
            
            try:
                # Perform enhanced analysis
                analysis_results = model.analyze_image(
                    image_path, 
                    save_mask=True, 
                    output_dir=output_dir,
                    save_confidence_mask=True,
                    save_combined=True
                )
                
                if analysis_results and analysis_results['localization']['mask'] is not None:
                    detection = analysis_results['detection']
                    localization = analysis_results['localization']
                    
                    # Store results
                    detection_result = {
                        "image": os.path.basename(image_path),
                        "is_forged": detection['is_forged'] if detection['result'] is not None else None,
                        "confidence": detection['probability'] if detection['probability'] is not None else None,
                        "status": "success" if detection['result'] is not None else "failed"
                    }
                    
                    localization_result = {
                        "image": os.path.basename(image_path),
                        "has_forgery": localization['has_forgery'],
                        "mask_size": localization['mask_size'],
                        "forgery_coverage": None
                    }
                    
                    if localization['has_forgery'] and localization['mask'] is not None:
                        mask = localization['mask']
                        forgery_pixels = mask.sum()
                        total_pixels = mask.size
                        forgery_percentage = (forgery_pixels / total_pixels) * 100
                        localization_result['forgery_coverage'] = forgery_percentage
                    
                    results['detection_results'].append(detection_result)
                    results['localization_results'].append(localization_result)
                    
                    if verbose:
                        if detection['result'] is not None:
                            print(f"  ✓ Detection: {'🔴 FORGED' if detection['is_forged'] else '🟢 REAL'} ({detection['probability']:.1%})")
                        else:
                            print(f"  ⚠ Detection: FAILED")
                        print(f"  ✓ Forgery: {'Yes' if localization['has_forgery'] else 'No'}")
                        
                        if localization['has_forgery'] and localization_result['forgery_coverage'] is not None:
                            print(f"  ✓ Coverage: {localization_result['forgery_coverage']:.1f}%")
                        
                        print(f"  ✓ Mask Size: {localization['mask_size']}")
                    
                    results['successful_tests'] += 1
                else:
                    if verbose:
                        print(f"  ❌ Analysis failed")
                    results['failed_tests'] += 1
                    
            except Exception as e:
                if verbose:
                    print(f"  ❌ Error: {e}")
                results['failed_tests'] += 1
        
        # Summary
        if verbose:
            print(f"\n{'='*60}")
            print("FOLDER TESTING SUMMARY")
            print(f"{'='*60}")
            print(f"Folder: {folder_path}")
            print(f"Total images: {results['total_images']}")
            print(f"Successful tests: {results['successful_tests']}")
            print(f"Failed tests: {results['failed_tests']}")
            
            print(f"\nOutput Files Created in '{output_dir}/':")
            print(f"  📁 Binary Masks: *_mask.png")
            print(f"  🎨 Confidence Masks: *_confidence_mask.png")
            print(f"  🖼️  Combined Images: *_combined.png")
            
            # Show detection summary
            forged_count = sum(1 for r in results['detection_results'] if r['is_forged'] == True)
            real_count = sum(1 for r in results['detection_results'] if r['is_forged'] == False)
            failed_count = sum(1 for r in results['detection_results'] if r['status'] == 'failed')
            
            print(f"\nDetection Summary:")
            print(f"  🔴 Forged: {forged_count}")
            print(f"  🟢 Real: {real_count}")
            print(f"  ❌ Failed: {failed_count}")
        
        results['success'] = True
        return results
        
    except Exception as e:
        print(f"❌ Folder testing failed: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return {"success": False, "error": str(e)}

def main():
    """Main function with command line argument parsing"""
    parser = argparse.ArgumentParser(description='Test all images in a designated folder')
    parser.add_argument('folder_path', help='Path to the folder containing images')
    parser.add_argument('-o', '--output', default='folder_test_output', 
                       help='Output directory for results (default: folder_test_output)')
    parser.add_argument('-q', '--quiet', action='store_true', 
                       help='Quiet mode (less verbose output)')
    
    args = parser.parse_args()
    
    # Test the folder
    results = test_folder_images(
        folder_path=args.folder_path,
        output_dir=args.output,
        verbose=not args.quiet
    )
    
    if results['success']:
        if not args.quiet:
            print(f"\n🎉 Folder testing completed successfully!")
        return True
    else:
        if not args.quiet:
            print(f"\n⚠️  Folder testing failed: {results.get('error', 'Unknown error')}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
