#!/usr/bin/env python3
"""
Debug script to understand how the model determines if an image is generated/forged.
This will show the raw model outputs and decision process.
"""

import sys
import os
import torch
import numpy as np
from PIL import Image

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hifi_model import HiFiModel
from utils.hifi_utils import one_hot_label_new, level_1_convert
import torch.nn.functional as F

def debug_detection(image_path):
    """Debug the detection process step by step"""
    print(f"=== Debugging Detection for: {image_path} ===")
    
    # Initialize model
    model = HiFiModel(verbose=True)
    
    try:
        with torch.no_grad():
            # Preprocess image
            img_input, _ = model._transform_image(image_path)
            print(f"Input tensor shape: {img_input.shape}")
            print(f"Input tensor range: [{img_input.min():.4f}, {img_input.max():.4f}]")
            
            # Extract features
            features = model.feature_extractor(img_input)
            print(f"Features type: {type(features)}")
            if isinstance(features, list):
                print(f"Features list length: {len(features)}")
                for i, feat in enumerate(features):
                    print(f"  Feature {i} shape: {feat.shape}")
            else:
                print(f"Features shape: {features.shape}")
            
            # Perform detection
            mask1_fea, mask1_binary, out0, out1, out2, out3 = model.detector(features, img_input)
            print(f"Detection outputs:")
            print(f"  out0 shape: {out0.shape}")
            print(f"  out1 shape: {out1.shape}")
            print(f"  out2 shape: {out2.shape}")
            print(f"  out3 shape: {out3.shape}")
            
            # Show raw logits from out3 (final classification layer)
            print(f"\nRaw logits (out3): {out3.cpu().numpy()}")
            
            # Apply softmax to get probabilities
            softmax_probs = F.softmax(out3, dim=1)
            print(f"Softmax probabilities: {softmax_probs.cpu().numpy()}")
            print(f"  Class 0 (Real) probability: {softmax_probs[0, 0]:.6f}")
            print(f"  Class 1 (Forged) probability: {softmax_probs[0, 1]:.6f}")
            
            # Get classification result using the model's method
            res, prob = one_hot_label_new(out3)
            res = level_1_convert(res)[0]
            
            print(f"\nModel's decision process:")
            print(f"  one_hot_label_new result: {res}")
            print(f"  one_hot_label_new probability: {prob[0]:.6f}")
            print(f"  level_1_convert result: {res}")
            
            # Show the decision logic
            print(f"\nDecision Logic:")
            print(f"  - one_hot_label_new computes: prob = 1 - softmax_prob[class_0]")
            print(f"  - This gives: prob = 1 - {softmax_probs[0, 0]:.6f} = {prob[0]:.6f}")
            print(f"  - level_1_convert: if argmax == 0 → 0 (Real), else → 1 (Forged)")
            print(f"  - Final decision: {res} ({'Forged' if res == 1 else 'Real'})")
            print(f"  - Confidence: {prob[0]:.4f} ({'High' if prob[0] > 0.7 else 'Medium' if prob[0] > 0.5 else 'Low'})")
            
            # Check if this matches the model's detect method
            model_result, model_prob = model.detect(image_path, verbose=False)
            print(f"\nModel.detect() result: {model_result}, probability: {model_prob:.6f}")
            
            return res, prob[0], softmax_probs.cpu().numpy()
            
    except Exception as e:
        print(f"Error during debugging: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        # Default to the JPG image that was detected as forged
        image_path = "../images_to_test/5F7A5162.jpg"
    
    if not os.path.exists(image_path):
        print(f"Image not found: {image_path}")
        sys.exit(1)
    
    result, probability, softmax_probs = debug_detection(image_path)
    
    if result is not None:
        print(f"\n=== SUMMARY ===")
        print(f"Image: {image_path}")
        print(f"Decision: {'FORGED' if result == 1 else 'REAL'}")
        print(f"Confidence: {probability:.4f}")
        print(f"Raw probabilities: Real={softmax_probs[0,0]:.4f}, Forged={softmax_probs[0,1]:.4f}")
