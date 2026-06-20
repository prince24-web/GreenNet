import sys
sys.path.insert(0, '.')
from src.vision import analyze_plant_image, is_vision_available
from PIL import Image, ImageDraw
import numpy as np
import os

print("=== AgriSense Vision Module Test ===\n")

# Check what mode we're in
status = is_vision_available()
print(f"Vision mode: {status['mode']}")
if status['mode'] == 'onnx':
    print(f"Model size: {status['model_size_mb']} MB")
print()

# Create 3 synthetic test images
os.makedirs("data/test_images", exist_ok=True)

def make_test_image(path, r, g, b, label):
    """Create a solid-color test image."""
    arr = np.full((224, 224, 3), [r, g, b], dtype=np.uint8)
    img = Image.fromarray(arr)
    # Add some noise to make it more realistic
    noise = np.random.randint(-20, 20, arr.shape, dtype=np.int16)
    arr2 = np.clip(arr.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    Image.fromarray(arr2).save(path)
    print(f"  Created: {label} ({path})")

print("Creating synthetic test images...")
make_test_image("data/test_images/yellow_leaf.jpg", 200, 170, 60, "Yellow leaf (virus sim)")
make_test_image("data/test_images/green_leaf.jpg",  60, 140, 50, "Green leaf (healthy sim)")
make_test_image("data/test_images/brown_patch.jpg", 100, 110, 70, "Brown patch (blight sim)")
print()

# Run analysis on each
test_images = [
    ("data/test_images/yellow_leaf.jpg", "Yellow leaf"),
    ("data/test_images/green_leaf.jpg",  "Green leaf"),
    ("data/test_images/brown_patch.jpg", "Brown patch"),
]

for path, label in test_images:
    print(f"--- {label} ---")
    result = analyze_plant_image(path)
    if result['success']:
        print(f"  Detected : {result['display_name']}")
        print(f"  Crop     : {result['crop']}")
        print(f"  Severity : {result['severity']}")
        print(f"  Confidence: {result['confidence']}%")
        print(f"  Method   : {result['method']}")
        print(f"\n  LLM context block:")
        print("  " + result['vision_context'].replace('\n', '\n  '))
    else:
        print(f"  ✗ Failed: {result.get('error')}")
    print()

print("=== Vision module working. Phase 4 complete. ===")