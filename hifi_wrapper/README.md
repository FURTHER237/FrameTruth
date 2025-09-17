# HiFi Wrapper

A self-contained wrapper for the HiFi-IFDL (Hierarchical Fine-Grained Image Forgery Detection and Localization) models.

## Features

- **Binary Classification**: Detect if an image is real or forged
- **Fine-grained Classification**: Classify the type of forgery
- **Pixel-level Localization**: Generate masks showing forged regions
- **Self-contained**: No external dependencies on the original HiFi-IFDL repository

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. The wrapper is ready to use! No additional setup required.

## Quick Start

```python
from hifi_model import HiFiModel

# Initialize the model
model = HiFiModel()

# Analyze an image
results = model.analyze_image("path/to/image.jpg")

# Or use individual functions
result, probability = model.detect("path/to/image.jpg")
mask = model.localize("path/to/image.jpg")
```

## API Reference

### HiFiModel

#### `__init__(weights_path=None, device=None, verbose=True)`
Initialize the HiFi model wrapper.

- `weights_path`: Path to model weights directory (optional)
- `device`: Device to use ('cuda', 'cpu', or None for auto-detect)
- `verbose`: Whether to print initialization messages

#### `detect(image_path, verbose=False)`
Perform binary classification (real/forged).

- `image_path`: Path to the image file
- `verbose`: Whether to print results
- Returns: `(result, probability)` where result is 0 (real) or 1 (forged)

#### `localize(image_path)`
Perform pixel-level forgery localization.

- `image_path`: Path to the image file
- Returns: Binary mask as numpy array (0=real, 1=forged)

#### `analyze_image(image_path, save_mask=True, output_dir="output")`
Perform complete analysis (detection + localization).

- `image_path`: Path to the image file
- `save_mask`: Whether to save the localization mask
- `output_dir`: Directory to save outputs
- Returns: Dictionary with analysis results

#### `save_localization_mask(mask, image_path, output_dir="output")`
Save localization mask as an image.

- `mask`: Binary mask as numpy array
- `image_path`: Original image path (for naming)
- `output_dir`: Output directory

#### `get_model_info()`
Get information about the loaded models.

- Returns: Dictionary with model information

## Example Usage

```python
from hifi_model import HiFiModel

# Initialize model
model = HiFiModel(verbose=True)

# Get model information
info = model.get_model_info()
print(f"Using device: {info['device']}")

# Analyze an image
results = model.analyze_image("test_image.jpg")

# Check results
if results['detection']['is_forged']:
    print("Image is forged!")
    if results['localization']['has_forgery']:
        print("Forgery regions detected in the image")
else:
    print("Image appears to be real")
```

## Testing

Run the test script to verify everything is working:

```bash
python test_with_image.py
```

## Model Architecture

The wrapper includes:

1. **HRNet (High-Resolution Network)**: Feature extraction backbone
2. **NLCDetection**: Classification and localization network
3. **IsolatingLossFunction**: Loss function for localization

## Requirements

- Python 3.7+
- PyTorch 1.11.0+
- See `requirements.txt` for complete list

## Notes

- The wrapper automatically handles device selection (CUDA/CPU)
- Models are set to evaluation mode for inference
- Batch normalization issues are handled automatically
- No pretrained weights are included - models will use random initialization unless weights are provided

## License

This wrapper is based on the HiFi-IFDL research paper. Please refer to the original repository for licensing information.
