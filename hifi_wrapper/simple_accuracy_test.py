#!/usr/bin/env python3
"""
Simple accuracy analysis
"""

import sys
import os
import torch
import torch.nn.functional as F
import numpy as np

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Analyzing model accuracy...")

try:
    from hifi_model import HiFiModel
    from utils.hifi_utils import one_hot_label_new, level_1_convert
    
    # Initialize model
    model = HiFiModel(verbose=False)
    print("✅ Model initialized")
    
    # Test with the real image
    image_path = "../images_to_test/DJI_0091-2.jpg"
    print(f"Testing image: {image_path}")
    
    with torch.no_grad():
        # Preprocess image
        img_input, original_size = model._transform_image(image_path)
        print(f"Input shape: {img_input.shape}")
        
        # Extract features
        features = model.feature_extractor(img_input)
        print(f"Features extracted: {len(features) if isinstance(features, list) else features.shape}")
        
        # Perform detection
        mask1_fea, mask1_binary, out0, out1, out2, out3 = model.detector(features, img_input)
        print(f"Detection output shape: {out3.shape}")
        
        # Analyze probabilities
        softmax_probs = F.softmax(out3, dim=1).cpu().numpy()[0]
        print(f"\nAll 14 class probabilities:")
        for i, prob in enumerate(softmax_probs):
            print(f"  Class {i:2d}: {prob:.6f}")
        
        # Show top 3
        top3_indices = np.argsort(softmax_probs)[-3:][::-1]
        print(f"\nTop 3 predictions:")
        for i, idx in enumerate(top3_indices):
            print(f"  {i+1}. Class {idx:2d}: {softmax_probs[idx]:.6f}")
        
        # Model decision
        res, prob = one_hot_label_new(out3)
        res = level_1_convert(res)[0]
        
        print(f"\nModel Decision:")
        print(f"  Result: {res} ({'Forged' if res == 1 else 'Real'})")
        print(f"  Probability: {prob[0]:.6f}")
        print(f"  Class 0 (Real) probability: {softmax_probs[0]:.6f}")
        print(f"  Class 1 (Forged) probability: {softmax_probs[1]:.6f}")
        
        # Analysis
        print(f"\nAccuracy Analysis:")
        if res == 1:
            print(f"  ❌ FALSE POSITIVE: Model says FORGED but image is REAL")
            print(f"  🔍 Class 0 (Real) has very low probability: {softmax_probs[0]:.6f}")
            print(f"  🔍 Model is {prob[0]:.1%} confident it's forged")
            
            # Check which class has highest probability
            max_class = np.argmax(softmax_probs)
            print(f"  🔍 Highest probability class: {max_class} with {softmax_probs[max_class]:.6f}")
            
            if softmax_probs[0] < 0.1:
                print(f"  ⚠️  Class 0 (Real) probability is extremely low - model is heavily biased")
        
        # Test localization
        if model.loss_function is not None:
            pred_mask, pred_mask_score = model.loss_function.inference(mask1_fea)
            forgery_pixels = pred_mask.sum().item()
            total_pixels = pred_mask.numel()
            forgery_percentage = (forgery_pixels / total_pixels) * 100
            
            print(f"\nLocalization:")
            print(f"  Forgery coverage: {forgery_percentage:.2f}%")
            print(f"  Confidence range: [{pred_mask_score.min():.4f}, {pred_mask_score.max():.4f}]")
            
            if forgery_percentage > 50:
                print(f"  ⚠️  High forgery coverage suggests false positive")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

