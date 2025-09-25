#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Improved HiFi Model with better accuracy and reduced false positives
"""

import os
import sys
import torch
import torch.nn.functional as F
import numpy as np
from PIL import Image

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'models'))
sys.path.insert(0, os.path.join(current_dir, 'utils'))

from hifi_model import HiFiModel
from utils import one_hot_label_new, level_1_convert

class ImprovedHiFiModel(HiFiModel):
    """
    Improved HiFi Model with better accuracy and reduced false positives
    
    Key improvements:
    1. Better decision logic to reduce false positives
    2. Confidence-based filtering
    3. Ensemble voting for more reliable results
    4. Preprocessing to reduce artifacts
    """
    
    def __init__(self, weights_path=None, device=None, verbose=True, 
                 confidence_threshold=0.95, real_threshold=0.2, 
                 use_ensemble=True, reduce_artifacts=True):
        """
        Initialize the improved HiFi model
        
        Args:
            weights_path (str): Path to model weights directory
            device (str): Device to use ('cuda', 'cpu', or None for auto-detect)
            verbose (bool): Whether to print initialization messages
            confidence_threshold (float): High confidence threshold for forgery detection (0.0-1.0)
            real_threshold (float): Threshold for classifying as real (0.0-1.0)
            use_ensemble (bool): Whether to use ensemble voting
            reduce_artifacts (bool): Whether to apply artifact reduction preprocessing
        """
        super().__init__(weights_path, device, verbose, confidence_threshold)
        
        self.real_threshold = real_threshold
        self.use_ensemble = use_ensemble
        self.reduce_artifacts = reduce_artifacts
        
        if self.verbose:
            print(f"Improved HiFi Model initialized with:")
            print(f"  - Confidence threshold: {confidence_threshold}")
            print(f"  - Real threshold: {real_threshold}")
            print(f"  - Ensemble voting: {use_ensemble}")
            print(f"  - Artifact reduction: {reduce_artifacts}")
    
    def _preprocess_image(self, image_path):
        """Apply preprocessing to reduce artifacts that cause false positives"""
        if not self.reduce_artifacts:
            return image_path
        
        try:
            # Load and process image
            with Image.open(image_path) as img:
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Apply slight smoothing to reduce compression artifacts
                img_array = np.array(img)
                
                # Apply gentle Gaussian blur to reduce JPEG artifacts
                from scipy import ndimage
                if len(img_array.shape) == 3:
                    for i in range(3):
                        img_array[:,:,i] = ndimage.gaussian_filter(img_array[:,:,i], sigma=0.5)
                
                # Convert back to PIL Image
                processed_img = Image.fromarray(img_array.astype(np.uint8))
                
                # Save temporary processed image
                temp_path = image_path.replace('.jpg', '_processed.jpg').replace('.png', '_processed.png')
                processed_img.save(temp_path, quality=95)
                
                return temp_path
                
        except Exception as e:
            if self.verbose:
                print(f"Warning: Preprocessing failed, using original image: {e}")
            return image_path
    
    def _get_detailed_probabilities(self, image_path):
        """Get detailed softmax probabilities for all classes"""
        try:
            with torch.no_grad():
                # Preprocess image
                img_input, original_size = self._transform_image(image_path)
                
                # Extract features
                features = self.feature_extractor(img_input)
                
                # Perform detection
                mask1_fea, mask1_binary, out0, out1, out2, out3 = self.detector(features, img_input)
                
                # Get softmax probabilities
                softmax_probs = F.softmax(out3, dim=1)
                probs_array = softmax_probs.cpu().numpy()[0]
                
                return probs_array, out3.cpu().numpy()[0]
                
        except Exception as e:
            if self.verbose:
                print(f"Error getting detailed probabilities: {e}")
            return None, None
    
    def improved_detect(self, image_path, verbose=False):
        """
        Improved detection with better accuracy and reduced false positives
        
        Args:
            image_path (str): Path to the image file
            verbose (bool): Whether to print detailed results
            
        Returns:
            tuple: (result, probability) where result is 0 (real) or 1 (forged)
        """
        try:
            # Apply preprocessing if enabled
            processed_path = self._preprocess_image(image_path)
            
            # Get detailed probabilities
            probs_array, raw_logits = self._get_detailed_probabilities(processed_path)
            
            if probs_array is None:
                return None, None
            
            # Extract key probabilities
            real_prob = probs_array[0]  # Class 0 (Real)
            max_other_prob = max(probs_array[1:])  # Highest non-real class
            max_other_idx = np.argmax(probs_array[1:]) + 1
            
            if verbose:
                print(f"Detailed Analysis for {os.path.basename(image_path)}:")
                print(f"  Real probability: {real_prob:.6f}")
                print(f"  Max other class: {max_other_idx} with {max_other_prob:.6f}")
                print(f"  Top 3 classes: {np.argsort(probs_array)[-3:][::-1]}")
            
            # Improved decision logic
            if self.use_ensemble:
                # Ensemble voting approach
                decisions = []
                
                # Method 1: Real threshold approach
                if real_prob > self.real_threshold and max_other_prob < 0.15:
                    decisions.append(0)  # Real
                else:
                    decisions.append(1)  # Forged
                
                # Method 2: Confidence threshold approach
                if max_other_prob > self.confidence_threshold:
                    decisions.append(1)  # Forged
                else:
                    decisions.append(0)  # Real
                
                # Method 3: Original model approach
                original_result, original_prob = self.detect(processed_path, verbose=False)
                decisions.append(original_result)
                
                # Vote
                real_votes = decisions.count(0)
                forged_votes = decisions.count(1)
                
                if real_votes > forged_votes:
                    result = 0
                    probability = real_prob
                else:
                    result = 1
                    probability = max_other_prob
                
                if verbose:
                    print(f"  Ensemble voting: {decisions} -> {result} ({'Real' if result == 0 else 'Forged'})")
                
            else:
                # Single improved method
                if real_prob > self.real_threshold and max_other_prob < 0.15:
                    result = 0  # Real
                    probability = real_prob
                elif max_other_prob > self.confidence_threshold:
                    result = 1  # Forged
                    probability = max_other_prob
                else:
                    # Default to real for uncertain cases
                    result = 0
                    probability = real_prob
                
                if verbose:
                    print(f"  Single method: {result} ({'Real' if result == 0 else 'Forged'})")
            
            # Clean up temporary processed image
            if processed_path != image_path and os.path.exists(processed_path):
                os.remove(processed_path)
            
            return result, probability
            
        except Exception as e:
            if self.verbose:
                print(f"Error in improved detection: {e}")
            return None, None
    
    def analyze_image_detailed(self, image_path):
        """Provide detailed analysis of why an image was classified as it was"""
        try:
            # Get detailed probabilities
            probs_array, raw_logits = self._get_detailed_probabilities(image_path)
            
            if probs_array is None:
                return None
            
            # Get improved result
            result, probability = self.improved_detect(image_path, verbose=True)
            
            analysis = {
                'result': result,
                'probability': probability,
                'real_probability': probs_array[0],
                'max_other_probability': max(probs_array[1:]),
                'max_other_class': np.argmax(probs_array[1:]) + 1,
                'all_probabilities': probs_array,
                'raw_logits': raw_logits,
                'top_3_classes': np.argsort(probs_array)[-3:][::-1],
                'decision_reason': self._get_decision_reason(probs_array, result)
            }
            
            return analysis
            
        except Exception as e:
            if self.verbose:
                print(f"Error in detailed analysis: {e}")
            return None
    
    def _get_decision_reason(self, probs_array, result):
        """Get human-readable reason for the decision"""
        real_prob = probs_array[0]
        max_other_prob = max(probs_array[1:])
        max_other_idx = np.argmax(probs_array[1:]) + 1
        
        if result == 0:  # Real
            if real_prob > self.real_threshold:
                return f"Classified as REAL: Real probability ({real_prob:.3f}) exceeds threshold ({self.real_threshold})"
            else:
                return f"Classified as REAL: Default decision due to low confidence in forgery"
        else:  # Forged
            if max_other_prob > self.confidence_threshold:
                return f"Classified as FORGED: Class {max_other_idx} probability ({max_other_prob:.3f}) exceeds confidence threshold ({self.confidence_threshold})"
            else:
                return f"Classified as FORGED: Ensemble voting or other decision logic"

def test_improved_accuracy():
    """Test the improved model on your images"""
    print("Testing Improved HiFi Model Accuracy")
    print("=" * 60)
    
    # Test images
    test_images = [
        "../images_to_test/DJI_0091-2.jpg",
        "../images_to_test/Screenshot 2024-08-28 160928.png"
    ]
    
    # Test with different configurations
    configurations = [
        {"confidence_threshold": 0.95, "real_threshold": 0.2, "use_ensemble": True, "name": "Ensemble + High Threshold"},
        {"confidence_threshold": 0.9, "real_threshold": 0.15, "use_ensemble": True, "name": "Ensemble + Medium Threshold"},
        {"confidence_threshold": 0.95, "real_threshold": 0.2, "use_ensemble": False, "name": "Single Method + High Threshold"},
    ]
    
    for config in configurations:
        print(f"\n{'='*60}")
        print(f"Testing: {config['name']}")
        print(f"{'='*60}")
        
        try:
            model = ImprovedHiFiModel(
                confidence_threshold=config['confidence_threshold'],
                real_threshold=config['real_threshold'],
                use_ensemble=config['use_ensemble'],
                verbose=False
            )
            
            for image_path in test_images:
                if os.path.exists(image_path):
                    print(f"\nTesting: {os.path.basename(image_path)}")
                    result, prob = model.improved_detect(image_path, verbose=True)
                    
                    if result is not None:
                        status = "✅ REAL" if result == 0 else "❌ FORGED"
                        print(f"  Result: {status} (confidence: {prob:.3f})")
                    else:
                        print(f"  Error: Could not process image")
        
        except Exception as e:
            print(f"Error testing configuration: {e}")

if __name__ == "__main__":
    test_improved_accuracy()
