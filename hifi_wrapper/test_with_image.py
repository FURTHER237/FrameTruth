#!/usr/bin/env python3
"""
Test script for HiFi wrapper with a sample image
"""

import sys
import os

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_imports():
    """Test if all imports work correctly"""
    print("=" * 60)
    print("Testing HiFi Wrapper Imports")
    print("=" * 60)
    
    try:
        from hifi_model import HiFiModel
        print("✓ HiFiModel wrapper imported successfully!")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_model_initialization():
    """Test model initialization"""
    print("\n" + "=" * 60)
    print("Testing Model Initialization")
    print("=" * 60)
    
    try:
        from hifi_model import HiFiModel
        
        print("Initializing HiFi Model...")
        model = HiFiModel(verbose=True)
        print("✓ Model initialized successfully!")
        
        # Get model info
        info = model.get_model_info()
        print(f"Model info: {info}")
        
        return model
    except Exception as e:
        print(f"✗ Model initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_image_analysis(model):
    """Test image analysis with a sample image"""
    print("\n" + "=" * 60)
    print("Testing Image Analysis")
    print("=" * 60)
    
    # Use a sample image from the original HiFi-IFDL dataset
    test_image_path = "../external/hifi_ifdl/data_dir/CASIA/CASIA1/fake/Sp_D_CNN_A_ani0049_ani0084_0266.jpg"
    
    if not os.path.exists(test_image_path):
        print(f"✗ Test image not found: {test_image_path}")
        return False
    
    try:
        print(f"Testing with image: {test_image_path}")
        
        # Test detection
        print("\nTesting image detection...")
        result, probability = model.detect(test_image_path, verbose=True)
        
        if result is not None:
            print("✓ Detection successful!")
        else:
            print("✗ Detection failed!")
            return False
        
        # Test localization
        print("\nTesting image localization...")
        mask = model.localize(test_image_path)
        
        if mask is not None:
            print("✓ Localization successful!")
            print(f"Mask shape: {mask.shape}")
            print(f"Forgery pixels: {mask.sum()}")
        else:
            print("✗ Localization failed!")
            return False
        
        # Test complete analysis
        print("\nTesting complete analysis...")
        results = model.analyze_image(test_image_path, save_mask=True)
        
        print("✓ Complete analysis successful!")
        print(f"Results: {results}")
        
        return True
        
    except Exception as e:
        print(f"✗ Image analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("HiFi Wrapper Test Suite")
    print("=" * 60)
    
    # Test imports
    if not test_imports():
        print("\n❌ Import tests failed!")
        return False
    
    # Test model initialization
    model = test_model_initialization()
    if model is None:
        print("\n❌ Model initialization failed!")
        return False
    
    # Test image analysis
    if not test_image_analysis(model):
        print("\n❌ Image analysis tests failed!")
        return False
    
    print("\n🎉 All tests passed! The HiFi wrapper is working correctly.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
