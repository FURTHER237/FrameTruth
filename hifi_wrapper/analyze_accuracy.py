

#!/usr/bin/env python3
"""
Detailed analysis script to understand model accuracy issues
"""

import sys
import os
import torch
import torch.nn.functional as F
import numpy as np

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def analyze_model_decision(image_path):
    """Analyze the model's decision process in detail"""
    print(f"\n{'='*80}")
    print(f"DETAILED ANALYSIS FOR: {os.path.basename(image_path)}")
    print(f"{'='*80}")
    
    try:
        from hifi_model import HiFiModel
        from utils.hifi_utils import one_hot_label_new, level_1_convert
        
        # Initialize model
        model = HiFiModel(verbose=False)
        
        with torch.no_grad():
            # Preprocess image
            img_input, original_size = model._transform_image(image_path)
            print(f"Input tensor shape: {img_input.shape}")
            print(f"Original image size: {original_size}")
            print(f"Input tensor range: [{img_input.min():.4f}, {img_input.max():.4f}]")
            
            # Extract features
            features = model.feature_extractor(img_input)
            print(f"\nFeature extraction:")
            print(f"  Features type: {type(features)}")
            if isinstance(features, list):
                print(f"  Number of feature maps: {len(features)}")
                for i, feat in enumerate(features):
                    print(f"    Feature {i} shape: {feat.shape}")
                    print(f"    Feature {i} range: [{feat.min():.4f}, {feat.max():.4f}]")
            
            # Perform detection
            mask1_fea, mask1_binary, out0, out1, out2, out3 = model.detector(features, img_input)
            print(f"\nDetection outputs:")
            print(f"  mask1_fea shape: {mask1_fea.shape}")
            print(f"  mask1_binary shape: {mask1_binary.shape}")
            print(f"  out0 shape: {out0.shape} (range: [{out0.min():.4f}, {out0.max():.4f}])")
            print(f"  out1 shape: {out1.shape} (range: [{out1.min():.4f}, {out1.max():.4f}])")
            print(f"  out2 shape: {out2.shape} (range: [{out2.min():.4f}, {out2.max():.4f}])")
            print(f"  out3 shape: {out3.shape} (range: [{out3.min():.4f}, {out3.max():.4f}])")
            
            # Analyze raw logits
            raw_logits = out3.cpu().numpy()[0]
            print(f"\nRaw logits (out3):")
            for i, logit in enumerate(raw_logits):
                print(f"  Class {i:2d}: {logit:8.4f}")
            
            # Apply softmax to get probabilities
            softmax_probs = F.softmax(out3, dim=1)
            probs_array = softmax_probs.cpu().numpy()[0]
            print(f"\nSoftmax probabilities:")
            for i, prob in enumerate(probs_array):
                print(f"  Class {i:2d}: {prob:.6f}")
            
            # Show top 3 predictions
            top3_indices = np.argsort(probs_array)[-3:][::-1]
            print(f"\nTop 3 predictions:")
            for i, idx in enumerate(top3_indices):
                print(f"  {i+1}. Class {idx:2d}: {probs_array[idx]:.6f}")
            
            # Analyze the decision logic
            print(f"\nDecision Analysis:")
            print(f"  Class 0 (Real) probability: {probs_array[0]:.6f}")
            print(f"  Class 1 (Forged) probability: {probs_array[1]:.6f}")
            
            # Get model's decision
            res, prob = one_hot_label_new(out3)
            res = level_1_convert(res)[0]
            
            print(f"\nModel's Decision Process:")
            print(f"  one_hot_label_new result: {res}")
            print(f"  one_hot_label_new probability: {prob[0]:.6f}")
            print(f"  level_1_convert result: {res}")
            
            # Show the decision logic
            print(f"\nDecision Logic Breakdown:")
            print(f"  - one_hot_label_new computes: prob = 1 - softmax_prob[class_0]")
            print(f"  - This gives: prob = 1 - {probs_array[0]:.6f} = {prob[0]:.6f}")
            print(f"  - level_1_convert: if argmax == 0 → 0 (Real), else → 1 (Forged)")
            print(f"  - Final decision: {res} ({'Forged' if res == 1 else 'Real'})")
            print(f"  - Confidence: {prob[0]:.4f} ({'High' if prob[0] > 0.7 else 'Medium' if prob[0] > 0.5 else 'Low'})")
            
            # Analyze why it might be wrong
            print(f"\nAccuracy Analysis:")
            if res == 1:  # Model says forged
                print(f"  ❌ Model classifies as FORGED with {prob[0]:.1%} confidence")
                print(f"  🔍 Possible reasons for false positive:")
                print(f"     - Class 0 (Real) has low probability: {probs_array[0]:.6f}")
                print(f"     - Other classes have higher probabilities")
                print(f"     - Model may be biased towards forgery detection")
                
                # Check if any other class has high probability
                max_other_class = max(probs_array[1:])
                max_other_idx = np.argmax(probs_array[1:]) + 1
                print(f"     - Highest non-real class: Class {max_other_idx} with {max_other_class:.6f}")
                
            else:  # Model says real
                print(f"  ✅ Model classifies as REAL with {prob[0]:.1%} confidence")
            
            # Test localization
            if model.loss_function is not None:
                pred_mask, pred_mask_score = model.loss_function.inference(mask1_fea)
                forgery_pixels = pred_mask.sum().item()
                total_pixels = pred_mask.numel()
                forgery_percentage = (forgery_pixels / total_pixels) * 100
                
                print(f"\nLocalization Analysis:")
                print(f"  Mask shape: {pred_mask.shape}")
                print(f"  Forgery coverage: {forgery_percentage:.2f}%")
                print(f"  Confidence range: [{pred_mask_score.min():.4f}, {pred_mask_score.max():.4f}]")
                print(f"  Mean confidence: {pred_mask_score.mean():.4f}")
                
                if forgery_percentage > 50:
                    print(f"  ⚠️  High forgery coverage ({forgery_percentage:.1f}%) - may indicate false positive")
            
            return {
                'result': res,
                'probability': prob[0],
                'softmax_probs': probs_array,
                'raw_logits': raw_logits,
                'top3_classes': top3_indices,
                'localization_coverage': forgery_percentage if model.loss_function else None
            }
            
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_multiple_images():
    """Test multiple images to understand the pattern"""
    print(f"\n{'='*80}")
    print("TESTING MULTIPLE IMAGES FOR ACCURACY ANALYSIS")
    print(f"{'='*80}")
    
    # Test with available images
    test_images = [
        "../images_to_test/DJI_0091-2.jpg",
        "../images_to_test/Screenshot 2024-08-28 160928.png"
    ]
    
    results = []
    for image_path in test_images:
        if os.path.exists(image_path):
            print(f"\nTesting: {os.path.basename(image_path)}")
            result = analyze_model_decision(image_path)
            if result:
                results.append({
                    'image': os.path.basename(image_path),
                    'result': result['result'],
                    'probability': result['probability'],
                    'top_class': result['top3_classes'][0],
                    'real_prob': result['softmax_probs'][0],
                    'localization_coverage': result['localization_coverage']
                })
    
    # Summary
    print(f"\n{'='*80}")
    print("ACCURACY SUMMARY")
    print(f"{'='*80}")
    
    for result in results:
        status = "❌ FORGED" if result['result'] == 1 else "✅ REAL"
        print(f"{result['image']:30} | {status:10} | {result['probability']:.3f} | Class {result['top_class']:2d} | Real: {result['real_prob']:.3f} | Coverage: {result['localization_coverage']:.1f}%")
    
    # Calculate false positive rate
    false_positives = sum(1 for r in results if r['result'] == 1)
    total_images = len(results)
    if total_images > 0:
        fp_rate = (false_positives / total_images) * 100
        print(f"\nFalse Positive Rate: {fp_rate:.1f}% ({false_positives}/{total_images})")
        
        if fp_rate > 50:
            print("⚠️  HIGH FALSE POSITIVE RATE - Model may be biased towards forgery detection")
            print("🔧 Recommendations:")
            print("   1. Adjust decision threshold")
            print("   2. Use ensemble methods")
            print("   3. Fine-tune on more diverse real images")
            print("   4. Implement confidence-based filtering")

def main():
    """Main analysis function"""
    print("HiFi Model Accuracy Analysis")
    
    # Analyze the specific image
    image_path = "../images_to_test/DJI_0091-2.jpg"
    if os.path.exists(image_path):
        analyze_model_decision(image_path)
    
    # Test multiple images
    test_multiple_images()

if __name__ == "__main__":
    main()

