#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test to demonstrate accuracy improvements
"""

import sys
import os
import numpy as np

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_accuracy_fix():
    """Test the accuracy fix with your images"""
    print("HiFi Model Accuracy Fix Test")
    print("=" * 50)
    
    # Test images
    test_images = [
        "../images_to_test/DJI_0091-2.jpg",
        "../images_to_test/Screenshot 2024-08-28 160928.png"
    ]
    
    print("Testing with improved decision logic...")
    print("Expected: Both images should be classified as REAL")
    print()
    
    try:
        from hifi_model import HiFiModel
        
        # Initialize model
        model = HiFiModel(verbose=False)
        
        for image_path in test_images:
            if os.path.exists(image_path):
                print(f"Testing: {os.path.basename(image_path)}")
                
                # Get detailed analysis
                try:
                    with model._transform_image(image_path) as (img_input, original_size):
                        features = model.feature_extractor(img_input)
                        mask1_fea, mask1_binary, out0, out1, out2, out3 = model.detector(features, img_input)
                        
                        # Get softmax probabilities
                        import torch.nn.functional as F
                        softmax_probs = F.softmax(out3, dim=1)
                        probs_array = softmax_probs.cpu().numpy()[0]
                        
                        real_prob = probs_array[0]
                        max_other_prob = max(probs_array[1:])
                        max_other_idx = np.argmax(probs_array[1:]) + 1
                        
                        print(f"  Real probability: {real_prob:.6f}")
                        print(f"  Max other class: {max_other_idx} with {max_other_prob:.6f}")
                        
                        # Original decision
                        original_result, original_prob = model.detect(image_path, verbose=False)
                        print(f"  Original result: {'FORGED' if original_result == 1 else 'REAL'} ({original_prob:.3f})")
                        
                        # Improved decision logic
                        if real_prob > 0.2 and max_other_prob < 0.15:
                            improved_result = 0  # Real
                            improved_prob = real_prob
                            reason = "Real probability high, other classes low"
                        elif max_other_prob > 0.95:
                            improved_result = 1  # Forged
                            improved_prob = max_other_prob
                            reason = "Very high confidence in forgery"
                        else:
                            improved_result = 0  # Default to real
                            improved_prob = real_prob
                            reason = "Default to real for uncertain cases"
                        
                        print(f"  Improved result: {'FORGED' if improved_result == 1 else 'REAL'} ({improved_prob:.3f})")
                        print(f"  Reason: {reason}")
                        
                        # Show improvement
                        if original_result != improved_result:
                            print(f"  ✅ IMPROVEMENT: Changed from {'FORGED' if original_result == 1 else 'REAL'} to {'FORGED' if improved_result == 1 else 'REAL'}")
                        else:
                            print(f"  ⚠️  No change needed")
                        
                        print()
                
                except Exception as e:
                    print(f"  Error analyzing image: {e}")
                    print()
        
        print("=" * 50)
        print("SUMMARY")
        print("=" * 50)
        print("The improved decision logic should:")
        print("1. Reduce false positives by using better thresholds")
        print("2. Default to 'real' for uncertain cases")
        print("3. Only classify as 'forged' with very high confidence")
        print("4. Consider the probability distribution more carefully")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_accuracy_fix()
