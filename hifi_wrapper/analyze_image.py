#!/usr/bin/env python3
"""
Simple script to analyze any image with the HiFi wrapper
Usage: python analyze_image.py <path_to_image>
"""

import sys
import os

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def analyze_image(image_path):
    """Analyze a single image"""
    try:
        from hifi_model import HiFiModel
        
        # Check if image exists
        if not os.path.exists(image_path):
            print(f"Error: Image not found: {image_path}")
            return False
        
        print(f"Analyzing image: {image_path}")
        print("=" * 50)
        
        # Initialize model
        print("Initializing HiFi Model...")
        model = HiFiModel(verbose=False)  # Less verbose for cleaner output
        print("✓ Model ready!")
        
        # Perform analysis
        print("\nPerforming analysis...")
        results = model.analyze_image(image_path, save_mask=True, output_dir="analysis_output")
        
        # Display results
        print("\n" + "=" * 50)
        print("ANALYSIS RESULTS")
        print("=" * 50)
        
        detection = results['detection']
        localization = results['localization']
        
        print(f"Image: {os.path.basename(image_path)}")
        print(f"Detection: {'🔴 FORGED' if detection['is_forged'] else '🟢 REAL'}")
        print(f"Confidence: {detection['probability']:.1%}")
        
        if localization['mask'] is not None:
            mask = localization['mask']
            forgery_pixels = mask.sum()
            total_pixels = mask.size
            forgery_percentage = (forgery_pixels / total_pixels) * 100
            
            print(f"Forgery Regions: {'Yes' if localization['has_forgery'] else 'No'}")
            if localization['has_forgery']:
                print(f"Forgery Coverage: {forgery_percentage:.1f}% of the image")
                print(f"Forgery Pixels: {forgery_pixels:.0f} out of {total_pixels}")
        
        print(f"\nLocalization mask saved to: analysis_output/{os.path.splitext(os.path.basename(image_path))[0]}_mask.png")
        
        return True
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python analyze_image.py <path_to_image>")
        print("\nExample:")
        print("  python analyze_image.py ../images_to_test/image1.jpg")
        print("  python analyze_image.py /path/to/your/image.jpg")
        return False
    
    image_path = sys.argv[1]
    return analyze_image(image_path)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
