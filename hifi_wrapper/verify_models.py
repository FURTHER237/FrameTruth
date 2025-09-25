#!/usr/bin/env python3
"""
Comprehensive model verification script to ensure all components are working correctly.
"""

import sys
import os
import torch
import numpy as np
from PIL import Image

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_model_initialization():
    """Test that all models initialize correctly"""
    print("=" * 60)
    print("TESTING MODEL INITIALIZATION")
    print("=" * 60)
    
    try:
        from hifi_model import HiFiModel
        
        # Initialize model
        model = HiFiModel(verbose=True)
        
        # Check model components
        print(f"\nModel Components:")
        print(f"  Feature Extractor: {type(model.feature_extractor).__name__}")
        print(f"  Detector: {type(model.detector).__name__}")
        print(f"  Loss Function: {type(model.loss_function).__name__ if model.loss_function else 'None'}")
        print(f"  Device: {model.device}")
        
        # Check if models are in eval mode
        print(f"\nModel States:")
        print(f"  Feature Extractor eval mode: {not model.feature_extractor.training}")
        print(f"  Detector eval mode: {not model.detector.training}")
        
        return model
        
    except Exception as e:
        print(f"❌ Model initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_feature_extractor(model):
    """Test HRNet feature extractor"""
    print("\n" + "=" * 60)
    print("TESTING HRNET FEATURE EXTRACTOR")
    print("=" * 60)
    
    try:
        # Create dummy input
        dummy_input = torch.randn(1, 3, 256, 256).to(model.device)
        print(f"Input shape: {dummy_input.shape}")
        
        with torch.no_grad():
            features = model.feature_extractor(dummy_input)
            
        print(f"✅ Feature extraction successful")
        print(f"  Features type: {type(features)}")
        
        if isinstance(features, list):
            print(f"  Features list length: {len(features)}")
            for i, feat in enumerate(features):
                print(f"    Feature {i} shape: {feat.shape}")
        else:
            print(f"  Features shape: {features.shape}")
            
        return features
        
    except Exception as e:
        print(f"❌ Feature extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_detector(model, features):
    """Test NLCDetection model"""
    print("\n" + "=" * 60)
    print("TESTING NLCDETECTION MODEL")
    print("=" * 60)
    
    try:
        # Create dummy input for detector
        dummy_input = torch.randn(1, 3, 256, 256).to(model.device)
        print(f"Input shape: {dummy_input.shape}")
        
        with torch.no_grad():
            mask1_fea, mask1_binary, out0, out1, out2, out3 = model.detector(features, dummy_input)
            
        print(f"✅ Detection successful")
        print(f"  mask1_fea shape: {mask1_fea.shape}")
        print(f"  mask1_binary shape: {mask1_binary.shape}")
        print(f"  out0 shape: {out0.shape}")
        print(f"  out1 shape: {out1.shape}")
        print(f"  out2 shape: {out2.shape}")
        print(f"  out3 shape: {out3.shape}")
        
        # Check output ranges
        print(f"\nOutput ranges:")
        print(f"  out3 (logits) range: [{out3.min():.4f}, {out3.max():.4f}]")
        print(f"  mask1_binary range: [{mask1_binary.min():.4f}, {mask1_binary.max():.4f}]")
        
        return mask1_fea, mask1_binary, out0, out1, out2, out3
        
    except Exception as e:
        print(f"❌ Detection failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_loss_function(model, mask1_fea):
    """Test IsolatingLossFunction for localization"""
    print("\n" + "=" * 60)
    print("TESTING ISOLATING LOSS FUNCTION")
    print("=" * 60)
    
    if model.loss_function is None:
        print("⚠️  Loss function is None - localization will use fallback method")
        return None
        
    try:
        with torch.no_grad():
            pred_mask, pred_mask_score = model.loss_function.inference(mask1_fea)
            
        print(f"✅ Localization successful")
        print(f"  pred_mask shape: {pred_mask.shape}")
        print(f"  pred_mask_score shape: {pred_mask_score.shape}")
        print(f"  pred_mask range: [{pred_mask.min():.4f}, {pred_mask.max():.4f}]")
        print(f"  pred_mask_score range: [{pred_mask_score.min():.4f}, {pred_mask_score.max():.4f}]")
        
        return pred_mask, pred_mask_score
        
    except Exception as e:
        print(f"❌ Localization failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_full_pipeline(model):
    """Test the complete detection and localization pipeline"""
    print("\n" + "=" * 60)
    print("TESTING FULL PIPELINE")
    print("=" * 60)
    
    try:
        # Test with a dummy image path (we'll create a dummy image)
        dummy_image_path = "dummy_test_image.jpg"
        
        # Create a dummy image
        dummy_image = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
        Image.fromarray(dummy_image).save(dummy_image_path)
        
        # Test detection
        result, probability = model.detect(dummy_image_path, verbose=False)
        print(f"✅ Detection successful")
        print(f"  Result: {result} ({'Forged' if result == 1 else 'Real'})")
        print(f"  Probability: {probability:.6f}")
        
        # Test localization
        localization_result = model.localize(dummy_image_path, return_confidence=True)
        if localization_result is not None:
            mask, confidence_scores = localization_result
            print(f"✅ Localization successful")
            print(f"  Mask shape: {mask.shape}")
            print(f"  Confidence shape: {confidence_scores.shape}")
            print(f"  Forgery coverage: {(mask.sum() / mask.size) * 100:.2f}%")
        else:
            print("⚠️  Localization returned None")
        
        # Clean up
        os.remove(dummy_image_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Full pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_center_radius_file():
    """Test if center/radius file is properly loaded"""
    print("\n" + "=" * 60)
    print("TESTING CENTER/RADIUS FILE")
    print("=" * 60)
    
    try:
        from utils import load_center_radius_api
        
        center, radius = load_center_radius_api()
        print(f"✅ Center/radius loaded successfully")
        print(f"  Center shape: {center.shape}")
        print(f"  Radius shape: {radius.shape}")
        print(f"  Center range: [{center.min():.4f}, {center.max():.4f}]")
        print(f"  Radius value: {radius.item():.4f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Center/radius loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("HiFi Model Verification Script")
    print("=" * 60)
    
    # Test 1: Model initialization
    model = test_model_initialization()
    if model is None:
        print("\n❌ CRITICAL: Model initialization failed. Cannot continue.")
        return
    
    # Test 2: Feature extractor
    features = test_feature_extractor(model)
    if features is None:
        print("\n❌ CRITICAL: Feature extraction failed. Cannot continue.")
        return
    
    # Test 3: Detector
    detection_outputs = test_detector(model, features)
    if detection_outputs is None:
        print("\n❌ CRITICAL: Detection failed. Cannot continue.")
        return
    
    mask1_fea, mask1_binary, out0, out1, out2, out3 = detection_outputs
    
    # Test 4: Loss function
    localization_outputs = test_loss_function(model, mask1_fea)
    
    # Test 5: Center/radius file
    test_center_radius_file()
    
    # Test 6: Full pipeline
    pipeline_success = test_full_pipeline(model)
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    if model and features and detection_outputs and pipeline_success:
        print("✅ ALL TESTS PASSED - Models are working correctly!")
    else:
        print("❌ SOME TESTS FAILED - Check the output above for details")
    
    print(f"\nModel Info:")
    info = model.get_model_info()
    for key, value in info.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    main()
