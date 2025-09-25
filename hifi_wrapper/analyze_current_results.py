#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyze current test results from HiFi wrapper
"""

import os
import glob
from PIL import Image
import numpy as np

def analyze_mask(mask_path):
    """Analyze a forgery mask"""
    try:
        mask = Image.open(mask_path)
        mask_array = np.array(mask)
        
        # Convert to binary if needed
        if len(mask_array.shape) == 3:
            mask_array = mask_array[:,:,0]  # Take first channel
        
        # Normalize to 0-1 range
        if mask_array.max() > 1:
            mask_array = mask_array / 255.0
        
        # Calculate statistics
        total_pixels = mask_array.size
        forgery_pixels = np.sum(mask_array > 0.5)
        forgery_percentage = (forgery_pixels / total_pixels) * 100
        
        return {
            'total_pixels': total_pixels,
            'forgery_pixels': forgery_pixels,
            'forgery_percentage': forgery_percentage,
            'has_forgery': forgery_pixels > 0,
            'mask_shape': mask_array.shape
        }
    except Exception as e:
        return {'error': str(e)}

def analyze_current_results():
    """Analyze current test results"""
    print("HiFi Wrapper - Current Test Results Analysis")
    print("=" * 60)
    
    # Check batch_output directory
    output_dir = 'batch_output'
    if os.path.exists(output_dir):
        print(f"\n📁 Analyzing {output_dir}:")
        
        # Find all mask files
        mask_files = glob.glob(os.path.join(output_dir, "*_mask.png"))
        confidence_files = glob.glob(os.path.join(output_dir, "*_confidence_mask.png"))
        
        print(f"  Found {len(mask_files)} mask files")
        print(f"  Found {len(confidence_files)} confidence mask files")
        
        for mask_file in mask_files:
            filename = os.path.basename(mask_file)
            image_name = filename.replace('_mask.png', '')
            
            print(f"\n  📸 {image_name}:")
            
            # Analyze mask
            mask_stats = analyze_mask(mask_file)
            if 'error' in mask_stats:
                print(f"    ❌ Error analyzing mask: {mask_stats['error']}")
            else:
                print(f"    Mask size: {mask_stats['mask_shape']}")
                print(f"    Total pixels: {mask_stats['total_pixels']:,}")
                print(f"    Forgery pixels: {mask_stats['forgery_pixels']:,}")
                print(f"    Forgery percentage: {mask_stats['forgery_percentage']:.2f}%")
                print(f"    Has forgery: {'Yes' if mask_stats['has_forgery'] else 'No'}")
                
                # Determine result
                if mask_stats['has_forgery']:
                    if mask_stats['forgery_percentage'] > 50:
                        result = "🔴 HIGHLY FORGED"
                    elif mask_stats['forgery_percentage'] > 10:
                        result = "🟡 MODERATELY FORGED"
                    else:
                        result = "🟠 SLIGHTLY FORGED"
                else:
                    result = "🟢 REAL"
                
                print(f"    Result: {result}")
        
        # Check for confidence masks
        if confidence_files:
            print(f"\n  📊 Confidence Analysis:")
            for conf_file in confidence_files:
                filename = os.path.basename(conf_file)
                image_name = filename.replace('_confidence_mask.png', '')
                
                conf_stats = analyze_mask(conf_file)
                if 'error' not in conf_stats:
                    print(f"    {image_name} confidence: {conf_stats['forgery_percentage']:.2f}%")
    else:
        print(f"❌ Output directory not found: {output_dir}")
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    if os.path.exists(output_dir):
        mask_files = glob.glob(os.path.join(output_dir, "*_mask.png"))
        if mask_files:
            print(f"Total images processed: {len(mask_files)}")
            print("Images from images_to_test folder have been successfully analyzed!")
        else:
            print("No images processed yet")
    else:
        print("No output directory found")

if __name__ == "__main__":
    analyze_current_results()
