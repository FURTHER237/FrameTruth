#!/usr/bin/env python3
"""
HiFi Model Wrapper - A self-contained wrapper for HiFi-IFDL models
"""

import os
import sys
import torch
import torch.nn as nn
import numpy as np
import imageio
from PIL import Image

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'models'))
sys.path.insert(0, os.path.join(current_dir, 'utils'))

from models.seg_hrnet import get_seg_model
from models.seg_hrnet_config import get_cfg_defaults
from models.NLCDetection_api import NLCDetection
from utils import restore_weight_helper, one_hot_label_new, level_1_convert
from utils import IsolatingLossFunction, load_center_radius_api

class HiFiModel:
    """
    HiFi Model Wrapper for Image Forgery Detection and Localization
    
    This wrapper provides a clean interface to the HiFi-IFDL models for:
    - Binary classification (real/forged)
    - Fine-grained forgery type classification
    - Pixel-level forgery localization
    """
    
    def __init__(self, weights_path=None, device=None, verbose=True, confidence_threshold=0.5, center_radius_dir=None, input_size=256):
        """
        Initialize the HiFi model wrapper
        
        Args:
            weights_path (str): Path to model weights directory
            device (str): Device to use ('cuda', 'cpu', or None for auto-detect)
            verbose (bool): Whether to print initialization messages
            confidence_threshold (float): Minimum confidence threshold for forgery detection (0.0-1.0)
            center_radius_dir (str | None): Directory containing radius_center.pth (defaults to weights_path or 'center')
            input_size (int): Square input size to resize images to (default 256)
        """
        self.verbose = verbose
        self.confidence_threshold = confidence_threshold
        # If center dir not specified, default to weights_path if provided, else 'center'
        self.center_radius_dir = center_radius_dir or weights_path or 'center'
        self.input_size = int(input_size)
        
        # Set device
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)
        
        if self.verbose:
            print(f"Using device: {self.device}")
            print(f"Confidence threshold: {self.confidence_threshold}")
            print(f"Center/Radius directory: {self.center_radius_dir}")
            print(f"Input size: {self.input_size}")
        
        # Initialize models
        try:
            cfg = get_cfg_defaults()
            self.feature_extractor = get_seg_model(cfg).to(self.device)
            self.detector = NLCDetection().to(self.device)
            
            # Wrap with DataParallel if multiple GPUs are available
            if torch.cuda.device_count() > 1:
                self.feature_extractor = nn.DataParallel(self.feature_extractor)
                self.detector = nn.DataParallel(self.detector)
            
            # Set models to evaluation mode to fix batch normalization issues
            self.feature_extractor.eval()
            self.detector.eval()
            
            if self.verbose:
                print("Models initialized successfully")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize models: {e}")
        
        # Load weights if provided
        if weights_path:
            self._load_weights(weights_path)
        
        # Initialize loss function for localization
        try:
            center, radius = load_center_radius_api(center_radius_dir=self.center_radius_dir, device=self.device)
            self.loss_function = IsolatingLossFunction(center, radius).to(self.device)
            if self.verbose:
                print("Loss function initialized successfully")
        except Exception as e:
            if self.verbose:
                print(f"Warning: Could not initialize loss function: {e}")
            self.loss_function = None
        
        if self.verbose:
            print("HiFi Model initialization complete!")
    
    def _load_weights(self, weights_path):
        """Load model weights from the specified path"""
        try:
            if self.verbose:
                print(f"Loading weights from: {weights_path}")
            
            # Load HRNet weights
            hrnet_path = os.path.join(weights_path, "HRNet")
            if os.path.exists(hrnet_path):
                self.feature_extractor = restore_weight_helper(self.feature_extractor, hrnet_path, 750001)
            
            # Load NLCDetection weights
            nlc_path = os.path.join(weights_path, "NLCDetection")
            if os.path.exists(nlc_path):
                self.detector = restore_weight_helper(self.detector, nlc_path, 750001)
            
            if self.verbose:
                print("Weights loaded successfully")
        except Exception as e:
            if self.verbose:
                print(f"Warning: Could not load weights: {e}")
    
    def _transform_image(self, image_path):
        """
        Transform image for model input
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            tuple: (preprocessed image tensor, original dimensions)
        """
        # Load image
        image = imageio.imread(image_path)
        
        # Handle RGBA images by converting to RGB
        if image.shape[2] == 4:  # RGBA
            # Convert RGBA to RGB by compositing over white background
            alpha = image[:, :, 3:4] / 255.0
            rgb = image[:, :, :3]
            white_bg = np.ones_like(rgb) * 255
            image = (rgb * alpha + white_bg * (1 - alpha)).astype(np.uint8)
        elif image.shape[2] == 3:  # RGB
            pass  # Already correct
        else:
            raise ValueError(f"Unsupported image format with {image.shape[2]} channels")
        
        original_image = Image.fromarray(image)
        
        # Store original dimensions
        original_size = original_image.size  # (width, height)
        
        # Resize to 256x256
        image = original_image.resize((self.input_size, self.input_size), resample=Image.BICUBIC)
        image = np.asarray(image)
        
        # Normalize to [0, 1]
        image = image.astype(np.float32) / 255.0
        
        # Convert to tensor and add batch dimension
        image = torch.from_numpy(image)
        image = image.permute(2, 0, 1)  # HWC to CHW
        
        # Apply ImageNet normalization expected by many backbones
        mean = torch.tensor([0.485, 0.456, 0.406], dtype=torch.float32).view(3, 1, 1)
        std = torch.tensor([0.229, 0.224, 0.225], dtype=torch.float32).view(3, 1, 1)
        image = (image - mean) / std
        
        image = torch.unsqueeze(image, 0)  # Add batch dimension
        
        return image.to(self.device), original_size
    
    def detect(self, image_path, verbose=False, use_threshold=True, tta=False, prob_mode='auto'):
        """
        Perform binary classification (real/forged)
        
        Args:
            image_path (str): Path to the image file
            verbose (bool): Whether to print results
            use_threshold (bool): Whether to use confidence threshold for decision
            
        Returns:
            tuple: (result, probability) where result is 0 (real) or 1 (forged)
        """
        try:
            with torch.no_grad():
                # Preprocess image
                img_input, _ = self._transform_image(image_path)
                
                # Extract features
                features = self.feature_extractor(img_input)
                
                def forward_once(tensor):
                    mask1_fea, mask1_binary, out0, out1, out2, out3 = self.detector(features if tensor is img_input else self.feature_extractor(tensor), tensor)
                    # Softmax over classes
                    x = torch.nn.functional.softmax(out3, dim=1)
                    prob_real = float(x[0, 0].detach().cpu().numpy())
                    # Default forged prob is 1 - P(real)
                    prob_forged_default = 1.0 - prob_real
                    # Alternative forged prob as x[:,1] if desired
                    prob_forged_x1 = float(x[0, 1].detach().cpu().numpy()) if x.shape[1] > 1 else prob_forged_default
                    # Choose prob mapping
                    prob_forged = prob_forged_x1 if prob_mode == 'x1' else prob_forged_default
                    # Argmax decision
                    res_indices = torch.argmax(x, dim=1)
                    res_argmax = int(level_1_convert(list(res_indices.cpu().numpy()))[0])
                    return res_argmax, prob_forged

                if not tta:
                    res_argmax, prob_forged = forward_once(img_input)
                else:
                    # Test-time augmentation: original, hflip, vflip, rot90, rot180, rot270
                    tensors = [img_input,
                               torch.flip(img_input, dims=[3]),  # hflip
                               torch.flip(img_input, dims=[2]),  # vflip
                               torch.rot90(img_input, k=1, dims=[2,3]),
                               torch.rot90(img_input, k=2, dims=[2,3]),
                               torch.rot90(img_input, k=3, dims=[2,3])]
                    probs = []
                    res_votes = []
                    for t in tensors:
                        r, p = forward_once(t)
                        res_votes.append(r)
                        probs.append(p)
                    prob_forged = float(np.mean(probs))
                    # Majority vote for argmax decisions
                    res_argmax = 1 if sum(res_votes) > len(res_votes)/2 else 0

                if use_threshold:
                    res = 1 if prob_forged >= self.confidence_threshold else 0
                else:
                    res = res_argmax
                
                if verbose:
                    self._print_detection_result(res, prob_forged)
                
                return res, prob_forged
        except Exception as e:
            if self.verbose:
                print(f"Detection failed: {e}")
            return None, None
    
    def localize(self, image_path, return_confidence=False):
        """
        Perform pixel-level forgery localization
        
        Args:
            image_path (str): Path to the image file
            return_confidence (bool): Whether to return confidence scores along with binary mask
            
        Returns:
            numpy.ndarray or tuple: Binary mask (0=real, 1=forged) resized to original image dimensions
                                   If return_confidence=True, returns (binary_mask, confidence_scores)
        """
        try:
            with torch.no_grad():
                # Preprocess image
                img_input, original_size = self._transform_image(image_path)
                
                # Extract features
                features = self.feature_extractor(img_input)
                
                # Perform detection and get mask features
                mask1_fea, mask1_binary, out0, out1, out2, out3 = self.detector(features, img_input)
                
                # Generate localization mask
                if self.loss_function is not None:
                    pred_mask, pred_mask_score = self.loss_function.inference(mask1_fea)
                    pred_mask_score = pred_mask_score.cpu().numpy()
                    
                    # Store confidence scores before thresholding
                    confidence_scores = pred_mask_score[0].copy()
                    
                    # Apply threshold (2.3 is the threshold used in the original code)
                    pred_mask_score[pred_mask_score < 2.3] = 0.0
                    pred_mask_score[pred_mask_score >= 2.3] = 1.0
                    
                    binary_mask = pred_mask_score[0]
                else:
                    # Fallback to binary mask from detector
                    binary_mask = mask1_binary.cpu().numpy()[0]
                    confidence_scores = binary_mask.copy()
                
                # Resize masks back to original image dimensions
                binary_mask = Image.fromarray((binary_mask * 255).astype(np.uint8))
                binary_mask = binary_mask.resize(original_size, resample=Image.NEAREST)
                binary_mask = np.asarray(binary_mask) / 255.0
                
                if return_confidence:
                    # Resize confidence scores
                    confidence_scores = Image.fromarray((confidence_scores * 255).astype(np.uint8))
                    confidence_scores = confidence_scores.resize(original_size, resample=Image.BICUBIC)
                    confidence_scores = np.asarray(confidence_scores) / 255.0
                    return binary_mask, confidence_scores
                
                return binary_mask
        except Exception as e:
            if self.verbose:
                print(f"Localization failed: {e}")
            return None
    
    def _print_detection_result(self, result, probability):
        """Print detection result in a formatted way"""
        if result == 1:
            decision = "Forged"
            confidence = (probability - 0.5) / 0.5
        else:
            decision = "Real"
            confidence = (0.5 - probability) / 0.5
        
        print(f"Image is {decision} with confidence {confidence*100:.1f}%")
    
    def analyze_image(self, image_path, save_mask=True, output_dir="output", save_confidence_mask=True, save_combined=True):
        """
        Perform complete analysis (detection + localization)
        
        Args:
            image_path (str): Path to the image file
            save_mask (bool): Whether to save the localization mask
            output_dir (str): Directory to save outputs
            save_confidence_mask (bool): Whether to save confidence-weighted mask
            save_combined (bool): Whether to save combined image with overlay
            
        Returns:
            dict: Analysis results
        """
        results = {}
        
        # Get original image dimensions for reference
        _, original_size = self._transform_image(image_path)
        results['original_size'] = original_size
        
        # Perform detection
        detection_result, probability = self.detect(image_path, verbose=True)
        results['detection'] = {
            'result': detection_result,
            'probability': probability,
            'is_forged': detection_result == 1
        }
        
        # Perform localization with confidence scores
        localization_result = self.localize(image_path, return_confidence=True)
        if localization_result is not None:
            mask, confidence_scores = localization_result
            results['localization'] = {
                'mask': mask,
                'confidence_scores': confidence_scores,
                'has_forgery': np.any(mask) if mask is not None else False,
                'mask_size': mask.shape if mask is not None else None
            }
            
            # Save masks if requested
            if save_mask and mask is not None:
                os.makedirs(output_dir, exist_ok=True)
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                
                # Save binary mask
                self.save_localization_mask(mask, image_path, output_dir)
                
                # Save confidence mask
                if save_confidence_mask:
                    confidence_path = os.path.join(output_dir, f"{base_name}_confidence_mask.png")
                    self.create_confidence_mask(confidence_scores, confidence_path)
                
                # Save combined image
                if save_combined:
                    combined_path = os.path.join(output_dir, f"{base_name}_combined.png")
                    self.create_combined_image(image_path, mask, confidence_scores, combined_path)
        else:
            results['localization'] = {
                'mask': None,
                'confidence_scores': None,
                'has_forgery': False,
                'mask_size': None
            }
        
        return results
    
    def create_confidence_mask(self, confidence_scores, output_path):
        """
        Create a confidence-weighted mask with color coding
        
        Args:
            confidence_scores (numpy.ndarray): Confidence scores for each pixel
            output_path (str): Path to save the confidence mask
        """
        try:
            # Normalize confidence scores to 0-1 range
            min_conf = confidence_scores.min()
            max_conf = confidence_scores.max()
            if max_conf > min_conf:
                normalized_conf = (confidence_scores - min_conf) / (max_conf - min_conf)
            else:
                normalized_conf = confidence_scores
            
            # Create RGB image with color coding
            # Red channel: confidence level (darker red = higher confidence)
            # Green/Blue channels: 0 for pure red
            height, width = normalized_conf.shape
            confidence_rgb = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Map confidence to red intensity (0-255)
            confidence_rgb[:, :, 0] = (normalized_conf * 255).astype(np.uint8)
            
            # Save the confidence mask
            confidence_image = Image.fromarray(confidence_rgb)
            confidence_image.save(output_path)
            
            if self.verbose:
                print(f"Confidence mask saved to: {output_path}")
                
        except Exception as e:
            if self.verbose:
                print(f"Failed to create confidence mask: {e}")
    
    def create_combined_image(self, original_image_path, mask, confidence_scores, output_path, alpha=0.6):
        """
        Create a combined image showing the original with confidence-weighted overlay
        
        Args:
            original_image_path (str): Path to the original image
            mask (numpy.ndarray): Binary mask
            confidence_scores (numpy.ndarray): Confidence scores
            output_path (str): Path to save the combined image
            alpha (float): Transparency of the overlay (0-1)
        """
        try:
            # Load original image
            original_image = Image.open(original_image_path)
            original_array = np.array(original_image)
            
            # Normalize confidence scores
            min_conf = confidence_scores.min()
            max_conf = confidence_scores.max()
            if max_conf > min_conf:
                normalized_conf = (confidence_scores - min_conf) / (max_conf - min_conf)
            else:
                normalized_conf = confidence_scores
            
            # Create overlay (red for forgery regions)
            overlay = np.zeros_like(original_array)
            overlay[:, :, 0] = (normalized_conf * 255).astype(np.uint8)  # Red channel
            
            # Apply mask to overlay (only show red where mask indicates forgery)
            overlay = overlay * mask[:, :, np.newaxis]
            
            # Blend original image with overlay
            combined_array = original_array.astype(np.float32)
            overlay_float = overlay.astype(np.float32)
            
            # Apply alpha blending
            combined_array = combined_array * (1 - alpha) + overlay_float * alpha
            combined_array = np.clip(combined_array, 0, 255).astype(np.uint8)
            
            # Save combined image
            combined_image = Image.fromarray(combined_array)
            combined_image.save(output_path)
            
            if self.verbose:
                print(f"Combined image saved to: {output_path}")
                
        except Exception as e:
            if self.verbose:
                print(f"Failed to create combined image: {e}")
    
    def save_localization_mask(self, mask, image_path, output_dir="output"):
        """
        Save localization mask as an image
        
        Args:
            mask (numpy.ndarray): Binary mask
            image_path (str): Original image path (for naming)
            output_dir (str): Output directory
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            # Get filename without extension
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            mask_path = os.path.join(output_dir, f"{base_name}_mask.png")
            
            # Convert mask to PIL Image and save
            mask_image = Image.fromarray((mask * 255).astype(np.uint8))
            mask_image.save(mask_path)
            
            if self.verbose:
                print(f"Localization mask saved to: {mask_path}")
        except Exception as e:
            if self.verbose:
                print(f"Failed to save mask: {e}")
    
    def get_model_info(self):
        """Get information about the loaded models"""
        info = {
            'device': str(self.device),
            'feature_extractor': type(self.feature_extractor).__name__,
            'detector': type(self.detector).__name__,
            'loss_function': type(self.loss_function).__name__ if self.loss_function else None,
            'cuda_available': torch.cuda.is_available(),
            'gpu_count': torch.cuda.device_count() if torch.cuda.is_available() else 0
        }
        return info
