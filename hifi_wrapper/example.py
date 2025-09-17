#!/usr/bin/env python3
"""
Simple example of how to use the HiFi wrapper
"""

from hifi_model import HiFiModel

def main():
    # Initialize the model
    print("Initializing HiFi Model...")
    model = HiFiModel(verbose=True)
    
    # Get model information
    info = model.get_model_info()
    print(f"\nModel Information:")
    print(f"Device: {info['device']}")
    print(f"CUDA Available: {info['cuda_available']}")
    print(f"GPU Count: {info['gpu_count']}")
    
    # Example image path (you can change this to your own image)
    image_path = "../external/hifi_ifdl/data_dir/CASIA/CASIA1/fake/Sp_D_CNN_A_ani0049_ani0084_0266.jpg"
    
    print(f"\nAnalyzing image: {image_path}")
    
    # Perform complete analysis
    results = model.analyze_image(image_path, save_mask=True, output_dir="example_output")
    
    # Display results
    print(f"\nAnalysis Results:")
    print(f"Detection Result: {'Forged' if results['detection']['is_forged'] else 'Real'}")
    print(f"Confidence: {results['detection']['probability']:.3f}")
    print(f"Has Forgery Regions: {results['localization']['has_forgery']}")
    
    if results['localization']['mask'] is not None:
        mask = results['localization']['mask']
        forgery_pixels = mask.sum()
        total_pixels = mask.size
        forgery_percentage = (forgery_pixels / total_pixels) * 100
        print(f"Forgery Coverage: {forgery_percentage:.2f}% of the image")

if __name__ == "__main__":
    main()
