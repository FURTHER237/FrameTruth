#!/usr/bin/env python3
"""
Test consistency of model predictions across multiple runs
"""

import sys
import os
import torch
import numpy as np

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hifi_model import HiFiModel

def test_consistency(image_path, num_runs=5):
    """Test if the model gives consistent results across multiple runs"""
    print(f"Testing consistency for: {image_path}")
    print(f"Number of runs: {num_runs}")
    print("=" * 60)
    
    results = []
    
    for i in range(num_runs):
        print(f"\nRun {i+1}:")
        print("-" * 20)
        
        # Initialize model fresh each time
        model = HiFiModel(verbose=False)
        
        # Test detection
        result, probability = model.detect(image_path, verbose=False)
        
        print(f"  Result: {result} ({'Forged' if result == 1 else 'Real'})")
        print(f"  Probability: {probability:.6f}")
        
        results.append((result, probability))
        
        # Clean up
        del model
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
    
    # Analyze consistency
    print(f"\n{'='*60}")
    print("CONSISTENCY ANALYSIS:")
    print(f"{'='*60}")
    
    results_array = np.array(results)
    unique_results = np.unique(results_array[:, 0])
    mean_prob = np.mean(results_array[:, 1])
    std_prob = np.std(results_array[:, 1])
    
    print(f"Unique results: {unique_results}")
    print(f"Mean probability: {mean_prob:.6f}")
    print(f"Std probability: {std_prob:.6f}")
    
    if len(unique_results) == 1:
        print("✅ CONSISTENT: All runs gave the same result")
    else:
        print("❌ INCONSISTENT: Different results across runs")
        print("This suggests non-deterministic behavior in the model")
    
    if std_prob < 0.001:
        print("✅ CONSISTENT: Probability values are very stable")
    else:
        print("⚠️  VARIABLE: Probability values vary across runs")
    
    return results

if __name__ == "__main__":
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        image_path = "../images_to_test/5F7A5162.jpg"
    
    if not os.path.exists(image_path):
        print(f"Image not found: {image_path}")
        sys.exit(1)
    
    test_consistency(image_path)
