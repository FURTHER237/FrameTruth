#!/usr/bin/env python3
"""
Accuracy improvement script with configurable thresholds
"""

import sys
import os
import glob
import argparse
import re
from typing import List, Tuple, Dict

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def infer_label_from_name(filename: str) -> int:
    """Infer label from filename.

    Returns 0 for REAL, 1 for FAKE.
    Recognizes substrings: real, reald, authentic => REAL; fake, forged => FAKE.
    Defaults to REAL if none matched.
    """
    name = filename.lower()
    # Fake indicators
    if any(token in name for token in ["fake", "forg", "forged", "deepfake"]):
        return 1
    # Real indicators (accept common misspelling 'reald')
    if any(token in name for token in ["real", "reald", "authentic", "genuine"]):
        return 0
    # Default assume real if unspecified
    return 0


def collect_dataset_images(data_dir: str, exts: List[str]) -> List[Tuple[str, int]]:
    """Collect (path, label) pairs from a directory based on filename."""
    patterns = []
    for ext in exts:
        patterns.append(os.path.join(data_dir, f"**/*.{ext}"))
        patterns.append(os.path.join(data_dir, f"*.{ext}"))
    paths: List[str] = []
    for pattern in patterns:
        paths.extend(glob.glob(pattern, recursive=True))
    # De-duplicate while preserving order
    seen = set()
    unique_paths: List[str] = []
    for p in paths:
        if p not in seen and os.path.isfile(p):
            seen.add(p)
            unique_paths.append(p)
    dataset: List[Tuple[str, int]] = []
    for p in unique_paths:
        label = infer_label_from_name(os.path.basename(p))
        dataset.append((p, label))
    return dataset


def test_accuracy_with_thresholds(dataset: List[Tuple[str, int]], thresholds: List[float], verbose: bool = True) -> Tuple[float, float, Dict[float, Dict]]:
    """Test accuracy with different confidence thresholds over a labeled dataset.

    dataset: list of (image_path, label) where label 0=REAL, 1=FAKE
    returns: (best_threshold, best_accuracy, results_by_threshold)
    """
    if verbose:
        print("=" * 80)
        print("ACCURACY IMPROVEMENT TESTING")
        print("=" * 80)
        print(f"Testing {len(dataset)} images with {len(thresholds)} thresholds")
        print()

    results: Dict[float, Dict] = {}

    for threshold in thresholds:
        if verbose:
            print(f"Testing with threshold: {threshold}")
            print("-" * 40)
        try:
            from hifi_model import HiFiModel
            model = HiFiModel(verbose=False, confidence_threshold=threshold)

            threshold_results = []
            correct = 0
            total = 0

            for image_path, true_label in dataset:
                if os.path.exists(image_path):
                    result, prob = model.detect(image_path, verbose=False)
                    # Coerce None cases: treat below-threshold as REAL by default
                    if result is None:
                        if prob is not None and prob >= threshold:
                            result = 1  # FORGED if confidence passes threshold
                        else:
                            result = 0  # REAL otherwise
                    if prob is None:
                        prob = 0.0
                    total += 1
                    is_correct = int(result) == int(true_label)
                    if is_correct:
                        correct += 1
                    if verbose:
                        image_name = os.path.basename(image_path)
                        status = "REAL" if result == 0 else "FORGED"
                        truth = "REAL" if true_label == 0 else "FORGED"
                        print(f"  {image_name:30} | pred={status:6} | true={truth:6} | p={prob:.3f}")

            accuracy = (correct / total) * 100 if total > 0 else 0.0

            results[threshold] = {
                'accuracy': accuracy,
                'correct': correct,
                'total': total,
            }

            if verbose:
                print(f"  Accuracy: {accuracy:.1f}% ({correct}/{total})")
                print()

        except Exception as e:
            if verbose:
                print(f"  Error with threshold {threshold}: {e}")
                print()

    if verbose:
        # Summary
        print("=" * 80)
        print("ACCURACY SUMMARY")
        print("=" * 80)
        print(f"{'Threshold':<10} | {'Accuracy':<10} | {'Correct':<8} | {'Total':<6}")
        print("-" * 50)

    best_threshold = None
    best_accuracy = -1.0

    for threshold in sorted(thresholds):
        if threshold in results:
            acc = results[threshold]['accuracy']
            correct = results[threshold]['correct']
            total = results[threshold]['total']
            if verbose:
                print(f"{threshold:<10} | {acc:<10.1f} | {correct:<8} | {total:<6}")
            if acc > best_accuracy:
                best_accuracy = acc
                best_threshold = threshold

    if verbose:
        print("-" * 50)
        print(f"Best threshold: {best_threshold} with {best_accuracy:.1f}% accuracy")
        print("\n" + "=" * 80)
        print("RECOMMENDATIONS")
        print("=" * 80)
        if best_accuracy >= 90:
            print(f"✅ RECOMMENDED: Use threshold {best_threshold} for high accuracy")
        elif best_accuracy >= 70:
            print(f"⚠️  MODERATE: Use threshold {best_threshold} but consider additional validation")
        else:
            print("❌ POOR: All thresholds show low accuracy. Consider:")
            print("   1. Using ensemble methods")
            print("   2. Fine-tuning the model")
            print("   3. Using additional validation techniques")

    return best_threshold if best_threshold is not None else 0.5, max(0.0, best_accuracy), results


def create_improved_model_example(best_threshold: float):
    """Create an example of how to use the improved model"""
    print("\n" + "=" * 80)
    print("IMPROVED MODEL USAGE EXAMPLE")
    print("=" * 80)

    example_code = f'''
# Example: Using the improved HiFi model with better accuracy

from hifi_model import HiFiModel

# Initialize with recommended confidence threshold for better accuracy
model = HiFiModel(confidence_threshold={best_threshold:.2f}, verbose=True)

# Test an image
result, probability = model.detect("path/to/image.jpg", verbose=True)

# The model will now be more conservative and less likely to produce false positives
# Only classify as "forged" if confidence >= threshold

if result == 0:
    print("Image is classified as REAL")
else:
    print("Image is classified as FORGED with high confidence")
'''

    print(example_code)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sweep thresholds for best average accuracy over a labeled dataset.")
    parser.add_argument("--data-dir", default=os.path.join(os.path.dirname(__file__), "..", "images_to_test"), help="Directory containing test images labeled via filenames (real/reald/fake)")
    parser.add_argument("--exts", nargs="*", default=["jpg", "jpeg", "png", "webp"], help="Image file extensions to include")
    parser.add_argument("--thresholds", nargs="*", type=float, default=[0.9,0.91,0.92,0.93,0.94,0.95,0.96,0.97,0.98,0.99], help="Confidence thresholds to test")
    parser.add_argument("--quiet", action="store_true", help="Reduce per-image logging")
    parser.add_argument("--weights", default=None, help="Path to weights directory containing HRNet/ and NLCDetection/")
    parser.add_argument("--use-argmax", action="store_true", help="Use argmax-based classification (ignore threshold gating)")
    parser.add_argument("--center-dir", default=os.path.join(os.path.dirname(__file__), 'center'), help="Directory containing radius_center.pth")
    parser.add_argument("--input-size", type=int, default=256, help="Square input size to resize images to")
    parser.add_argument("--tta", action="store_true", help="Enable test-time augmentation (flips/rotations)")
    parser.add_argument("--prob-mode", choices=["auto","x1"], default="auto", help="Forged probability: auto=1-P(real), x1=softmax class 1")
    return parser.parse_args()


def main():
    """Main function"""
    print("HiFi Model Accuracy Improvement")

    args = parse_args()

    data_dir = os.path.abspath(args.data_dir)
    if not os.path.isdir(data_dir):
        print(f"Warning: data dir not found: {data_dir}")
        # Fallback to a tiny built-in set if exists
        fallback_images = [
            os.path.join(os.path.dirname(__file__), "..", "images_to_test", "DJI_0091-2.jpg"),
            os.path.join(os.path.dirname(__file__), "..", "images_to_test", "Screenshot 2024-08-28 160928.png"),
        ]
        dataset = [(p, infer_label_from_name(os.path.basename(p))) for p in fallback_images if os.path.exists(p)]
    else:
        dataset = collect_dataset_images(data_dir, args.exts)

    if len(dataset) == 0:
        print("No images found to evaluate.")
        return

    # Monkey-patch decision mode by temporarily setting threshold behavior
    # We pass the choice into HiFiModel by toggling use_threshold in detect calls via wrapper
    def evaluate_dataset(thresholds: List[float]):
        results = {}
        from hifi_model import HiFiModel
        for threshold in thresholds:
            model = HiFiModel(verbose=False, confidence_threshold=threshold, weights_path=args.weights, center_radius_dir=args.center_dir, input_size=args.input_size)
            correct = 0
            total = 0
            for image_path, true_label in dataset:
                if os.path.exists(image_path):
                    # When using argmax, bypass threshold gating by calling with use_threshold=False
                    result, prob = model.detect(image_path, verbose=False, use_threshold=not args.use_argmax, tta=args.tta, prob_mode=args.prob_mode)
                    if result is None:
                        # Coerce None similarly as earlier logic
                        if prob is not None and prob >= threshold:
                            result = 1
                        else:
                            result = 0
                    if prob is None:
                        prob = 0.0
                    total += 1
                    if int(result) == int(true_label):
                        correct += 1
            accuracy = (correct / total) * 100 if total > 0 else 0.0
            results[threshold] = { 'accuracy': accuracy, 'correct': correct, 'total': total }
        return results

    thresholds = args.thresholds
    results = evaluate_dataset(thresholds)

    # Reporting (reuse existing summary style)
    print("=" * 80)
    print("ACCURACY SUMMARY")
    print("=" * 80)
    print(f"{'Threshold':<10} | {'Accuracy':<10} | {'Correct':<8} | {'Total':<6}")
    print("-" * 50)

    best_threshold = None
    best_accuracy = -1.0
    for t in sorted(results.keys()):
        r = results[t]
        print(f"{t:<10} | {r['accuracy']:<10.1f} | {r['correct']:<8} | {r['total']:<6}")
        if r['accuracy'] > best_accuracy:
            best_accuracy = r['accuracy']
            best_threshold = t

    print("-" * 50)
    print(f"Best threshold: {best_threshold} with {best_accuracy:.1f}% accuracy")

    create_improved_model_example(best_threshold)

    print(f"\n🎯 CONCLUSION: Use confidence_threshold={best_threshold} for {best_accuracy:.1f}% accuracy")


if __name__ == "__main__":
    main()

