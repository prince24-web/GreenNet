"""
Downloads a pre-trained PlantVillage MobileNetV3 ONNX model.
Source: ONNX Model Zoo / community PlantVillage conversion.
"""
import os
import urllib.request

MODEL_URL = "https://github.com/spMohanty/PlantVillage-Dataset/releases/download/v1/mobilenetv3_plantvillage.onnx"
MODEL_PATH = "data/models/plant_disease.onnx"

# Fallback: we'll create a working mock if download fails
def download_model():
    os.makedirs("data/models", exist_ok=True)
    
    if os.path.exists(MODEL_PATH):
        size = os.path.getsize(MODEL_PATH) / (1024*1024)
        print(f"✓ Model already exists ({size:.1f} MB)")
        return True

    print("Downloading PlantVillage MobileNetV3 ONNX model...")
    print("This may take 2-3 minutes depending on connection...\n")

    try:
        def show_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            if total_size > 0:
                pct = min(100, downloaded * 100 / total_size)
                mb = downloaded / (1024*1024)
                print(f"\r  {pct:.1f}% — {mb:.1f} MB", end='', flush=True)

        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH, show_progress)
        print(f"\n✓ Model downloaded to {MODEL_PATH}")
        return True
    except Exception as e:
        print(f"\n✗ Download failed: {e}")
        print("→ Will use rule-based fallback vision system instead")
        return False

if __name__ == "__main__":
    download_model()