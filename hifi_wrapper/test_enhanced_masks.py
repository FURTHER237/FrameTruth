#!/usr/bin/env python3
"""
Test script for enhanced mask features with confidence weighting and combined images
"""

import sys
import os

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_enhanced_masks(image_path):
    """Test enhanced mask features"""
    try:
        from hifi_model import HiFiModel
        
        print("HiFi Wrapper - Enhanced Mask Testing")
        print("=" * 60)
        
        # Check if image exists
        if not os.path.exists(image_path):
            print(f"❌ Image not found: {image_path}")
            return False
        
        print(f"Testing image: {os.path.basename(image_path)}")
        print(f"Path: {image_path}")
        
        # Initialize model
        print(f"\nInitializing HiFi Model...")
        model = HiFiModel(verbose=False)
        print("✓ Model ready!")
        
        # Perform enhanced analysis
        print(f"\nPerforming enhanced analysis...")
        results = model.analyze_image(
            image_path, 
            save_mask=True, 
            output_dir="enhanced_output",
            save_confidence_mask=True,
            save_combined=True
        )
        
        if results is None:
            print("❌ Analysis failed!")
            return False
        
        # Display results
        print(f"\n" + "=" * 60)
        print("ENHANCED ANALYSIS RESULTS")
        print("=" * 60)
        
        detection = results['detection']
        localization = results['localization']
        
        print(f"Detection Result:")
        print(f"  Status: {'🔴 FORGED' if detection['is_forged'] else '🟢 REAL'}")
        print(f"  Confidence: {detection['probability']:.1%}")
        
        if localization['mask'] is not None:
            mask = localization['mask']
            confidence_scores = localization['confidence_scores']
            forgery_pixels = mask.sum()
            total_pixels = mask.size
            forgery_percentage = (forgery_pixels / total_pixels) * 100
            
            print(f"\nLocalization Result:")
            print(f"  Forgery Regions: {'Yes' if localization['has_forgery'] else 'No'}")
            print(f"  Mask Size: {mask.shape}")
            print(f"  Forgery Coverage: {forgery_percentage:.2f}% of the image")
            print(f"  Forgery Pixels: {forgery_pixels:.0f} out of {total_pixels:,}")
            
            # Confidence statistics
            if confidence_scores is not None:
                min_conf = confidence_scores.min()
                max_conf = confidence_scores.max()
                mean_conf = confidence_scores.mean()
                print(f"\nConfidence Statistics:")
                print(f"  Min Confidence: {min_conf:.3f}")
                print(f"  Max Confidence: {max_conf:.3f}")
                print(f"  Mean Confidence: {mean_conf:.3f}")
        
        print(f"\nOutput Files Created:")
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        print(f"  📁 Binary Mask: enhanced_output/{base_name}_mask.png")
        print(f"  🎨 Confidence Mask: enhanced_output/{base_name}_confidence_mask.png")
        print(f"  🖼️  Combined Image: enhanced_output/{base_name}_combined.png")
        
        print(f"\nMask Types:")
        print(f"  • Binary Mask: Black/white mask showing forgery regions")
        print(f"  • Confidence Mask: Red intensity shows confidence level")
        print(f"    - Darker red = Higher confidence the pixel is forged")
        print(f"    - Lighter red = Lower confidence")
        print(f"  • Combined Image: Original image with red overlay")
        print(f"    - Red overlay shows forgery regions with confidence weighting")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python test_enhanced_masks.py <path_to_image>")
        print("\nExamples:")
        print("  python test_enhanced_masks.py ../images_to_test/image1.jpg")
        print("  python test_enhanced_masks.py ../images_to_test/1a-1.webp")
        return False
    
    image_path = sys.argv[1]
    return test_enhanced_masks(image_path)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
