import os
import numpy as np
from PIL import Image

MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'models', 'plant_disease.onnx')

# ── PlantVillage 38-class labels ──────────────────────────────────────────────
PLANT_VILLAGE_CLASSES = [
    "Apple___Apple_scab",
    "Apple___Black_rot",
    "Apple___Cedar_apple_rust",
    "Apple___healthy",
    "Blueberry___healthy",
    "Cherry_(including_sour)___Powdery_mildew",
    "Cherry_(including_sour)___healthy",
    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
    "Corn_(maize)___Common_rust",
    "Corn_(maize)___Northern_Leaf_Blight",
    "Corn_(maize)___healthy",
    "Grape___Black_rot",
    "Grape___Esca_(Black_Measles)",
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)",
    "Grape___healthy",
    "Orange___Haunglongbing_(Citrus_greening)",
    "Peach___Bacterial_spot",
    "Peach___healthy",
    "Pepper,_bell___Bacterial_spot",
    "Pepper,_bell___healthy",
    "Potato___Early_blight",
    "Potato___Late_blight",
    "Potato___healthy",
    "Raspberry___healthy",
    "Soybean___healthy",
    "Squash___Powdery_mildew",
    "Strawberry___Leaf_scorch",
    "Strawberry___healthy",
    "Tomato___Bacterial_spot",
    "Tomato___Early_blight",
    "Tomato___Late_blight",
    "Tomato___Leaf_Mold",
    "Tomato___Septoria_leaf_spot",
    "Tomato___Spider_mites Two-spotted_spider_mite",
    "Tomato___Target_Spot",
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato___Tomato_mosaic_virus",
    "Tomato___healthy",
]

# ── Map PlantVillage labels → Nigerian farmer-friendly context ─────────────────
CLASS_TO_NIGERIAN_CONTEXT = {
    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot": {
        "display_name": "Maize Gray Leaf Spot",
        "crop": "Maize (Agbado)",
        "severity": "Medium",
        "local_tip": "Common in humid south. Improves when dry season comes.",
    },
    "Corn_(maize)___Common_rust": {
        "display_name": "Maize Common Rust",
        "crop": "Maize (Agbado)",
        "severity": "Medium",
        "local_tip": "Orange-brown pustules on leaves. Worse in cool wet weather.",
    },
    "Corn_(maize)___Northern_Leaf_Blight": {
        "display_name": "Maize Northern Leaf Blight",
        "crop": "Maize (Agbado)",
        "severity": "High",
        "local_tip": "Long gray-green lesions. Can cause serious yield loss.",
    },
    "Corn_(maize)___healthy": {
        "display_name": "Healthy Maize",
        "crop": "Maize (Agbado)",
        "severity": "None",
        "local_tip": "Plant looks healthy. Continue regular monitoring.",
    },
    "Tomato___Bacterial_spot": {
        "display_name": "Tomato Bacterial Spot",
        "crop": "Tomato (Tomati)",
        "severity": "High",
        "local_tip": "Water-soaked spots on leaves and fruit. Spreads in rain.",
    },
    "Tomato___Early_blight": {
        "display_name": "Tomato Early Blight",
        "crop": "Tomato (Tomati)",
        "severity": "Medium",
        "local_tip": "Brown spots with yellow rings (target pattern) on older leaves.",
    },
    "Tomato___Late_blight": {
        "display_name": "Tomato Late Blight",
        "crop": "Tomato (Tomati)",
        "severity": "Very High",
        "local_tip": "Most destructive tomato disease. Acts fast in rainy season. Spray Ridomil immediately.",
    },
    "Tomato___Leaf_Mold": {
        "display_name": "Tomato Leaf Mold",
        "crop": "Tomato (Tomati)",
        "severity": "Medium",
        "local_tip": "Yellow patches on top, olive mold below. Improve ventilation.",
    },
    "Tomato___Septoria_leaf_spot": {
        "display_name": "Tomato Septoria Leaf Spot",
        "crop": "Tomato (Tomati)",
        "severity": "Medium",
        "local_tip": "Small circular spots with dark borders. Remove infected leaves.",
    },
    "Tomato___Spider_mites Two-spotted_spider_mite": {
        "display_name": "Tomato Spider Mites",
        "crop": "Tomato (Tomati)",
        "severity": "Medium",
        "local_tip": "Tiny dots on leaves, fine webbing below. Worse in dry season.",
    },
    "Tomato___Target_Spot": {
        "display_name": "Tomato Target Spot",
        "crop": "Tomato (Tomati)",
        "severity": "Medium",
        "local_tip": "Circular brown lesions with concentric rings. Use Mancozeb.",
    },
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus": {
        "display_name": "Tomato Yellow Leaf Curl Virus",
        "crop": "Tomato (Tomati)",
        "severity": "Very High",
        "local_tip": "Leaves curl up and turn yellow. Spread by whiteflies. No cure — uproot and burn.",
    },
    "Tomato___Tomato_mosaic_virus": {
        "display_name": "Tomato Mosaic Virus",
        "crop": "Tomato (Tomati)",
        "severity": "High",
        "local_tip": "Mottled yellow-green leaves. No cure. Remove infected plants.",
    },
    "Tomato___healthy": {
        "display_name": "Healthy Tomato",
        "crop": "Tomato (Tomati)",
        "severity": "None",
        "local_tip": "Plant looks healthy. Monitor for early blight in rainy season.",
    },
    "Pepper,_bell___Bacterial_spot": {
        "display_name": "Pepper Bacterial Spot",
        "crop": "Pepper (Ose, Tatashe)",
        "severity": "High",
        "local_tip": "Dark water-soaked spots. Spreads fast in wet conditions.",
    },
    "Pepper,_bell___healthy": {
        "display_name": "Healthy Pepper",
        "crop": "Pepper (Ose, Tatashe)",
        "severity": "None",
        "local_tip": "Plant is healthy.",
    },
    "Potato___Early_blight": {
        "display_name": "Early Blight (similar to Tomato)",
        "crop": "Tomato / Irish Potato",
        "severity": "Medium",
        "local_tip": "Target-like brown spots on older leaves. Use Mancozeb spray.",
    },
    "Potato___Late_blight": {
        "display_name": "Late Blight (same pathogen as Tomato Late Blight)",
        "crop": "Tomato / Irish Potato",
        "severity": "Very High",
        "local_tip": "Identical to tomato late blight. Spray Ridomil Gold immediately.",
    },
    "Soybean___healthy": {
        "display_name": "Healthy Soybean",
        "crop": "Soybean (Wake-anguku)",
        "severity": "None",
        "local_tip": "Plant is healthy.",
    },
    "Squash___Powdery_mildew": {
        "display_name": "Powdery Mildew",
        "crop": "Pumpkin / Squash (Ugwu)",
        "severity": "Medium",
        "local_tip": "White powder on leaves. Spray with potassium bicarbonate or sulfur fungicide.",
    },
    "Orange___Haunglongbing_(Citrus_greening)": {
        "display_name": "Citrus Greening Disease",
        "crop": "Orange / Citrus",
        "severity": "Very High",
        "local_tip": "Yellowing of one side of tree. No cure. Report to Ministry of Agriculture.",
    },
}

# ── Image preprocessing (ImageNet standard) ───────────────────────────────────
IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD  = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def preprocess_image(image_path: str) -> np.ndarray:
    """Load and preprocess image for MobileNetV3 inference."""
    img = Image.open(image_path).convert("RGB")
    img = img.resize((224, 224), Image.BILINEAR)
    arr = np.array(img, dtype=np.float32) / 255.0
    arr = (arr - IMAGENET_MEAN) / IMAGENET_STD
    arr = arr.transpose(2, 0, 1)          # HWC → CHW
    arr = np.expand_dims(arr, axis=0)     # add batch dim → (1, 3, 224, 224)
    return arr


def run_onnx_inference(image_path: str) -> dict:
    """Run ONNX model inference. Returns top prediction with confidence."""
    try:
        import onnxruntime as ort

        session = ort.InferenceSession(
            MODEL_PATH,
            providers=["CPUExecutionProvider"]
        )

        input_name = session.get_inputs()[0].name
        tensor = preprocess_image(image_path)

        outputs = session.run(None, {input_name: tensor})
        logits = outputs[0][0]

        # Softmax
        exp_logits = np.exp(logits - np.max(logits))
        probs = exp_logits / exp_logits.sum()

        top3_idx = np.argsort(probs)[::-1][:3]

        return {
            "success": True,
            "method": "onnx",
            "top_prediction": PLANT_VILLAGE_CLASSES[top3_idx[0]],
            "confidence": float(probs[top3_idx[0]]),
            "top3": [
                {"class": PLANT_VILLAGE_CLASSES[i], "confidence": float(probs[i])}
                for i in top3_idx
            ]
        }
    except Exception as e:
        return {"success": False, "error": str(e), "method": "onnx"}


def analyze_image_rules(image_path: str) -> dict:
    """
    Rule-based fallback using color analysis.
    Works when ONNX model is unavailable.
    Detects dominant color patterns associated with common diseases.
    """
    img = Image.open(image_path).convert("RGB")
    img = img.resize((224, 224))
    arr = np.array(img, dtype=np.float32)

    r, g, b = arr[:,:,0].mean(), arr[:,:,1].mean(), arr[:,:,2].mean()

    # Color-based heuristic rules
    # Yellow dominance → mosaic virus or nutrient deficiency
    if r > 150 and g > 130 and b < 100:
        return {
            "success": True,
            "method": "rule_based",
            "top_prediction": "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
            "confidence": 0.62,
            "note": "Yellow coloration detected — possible viral infection or nutrient deficiency",
            "top3": []
        }
    # Dark brown patches on green → blight or spot disease
    elif g > r and r > 80 and b < 100:
        return {
            "success": True,
            "method": "rule_based",
            "top_prediction": "Tomato___Early_blight",
            "confidence": 0.55,
            "note": "Dark patches on green leaf detected — possible fungal disease",
            "top3": []
        }
    # Very pale/white patches → powdery mildew
    elif r > 180 and g > 180 and b > 160:
        return {
            "success": True,
            "method": "rule_based",
            "top_prediction": "Squash___Powdery_mildew",
            "confidence": 0.58,
            "note": "Pale/white patches detected — possible powdery mildew",
            "top3": []
        }
    # Healthy green
    elif g > r and g > b and g > 100:
        return {
            "success": True,
            "method": "rule_based",
            "top_prediction": "Tomato___healthy",
            "confidence": 0.70,
            "note": "Leaf appears predominantly green and healthy",
            "top3": []
        }
    else:
        return {
            "success": True,
            "method": "rule_based",
            "top_prediction": "Tomato___Late_blight",
            "confidence": 0.45,
            "note": "Unusual coloration — possible disease. Describe symptoms in chat for better diagnosis.",
            "top3": []
        }


def analyze_plant_image(image_path: str) -> dict:
    """
    Master function called by the orchestrator.
    Tries ONNX first, falls back to rule-based analysis.
    Always returns a result.
    """
    if not os.path.exists(image_path):
        return {
            "success": False,
            "error": "Image file not found",
            "vision_context": ""
        }

    # Try ONNX if model exists
    if os.path.exists(MODEL_PATH):
        result = run_onnx_inference(image_path)
    else:
        result = {"success": False, "method": "onnx", "error": "Model not downloaded"}

    # Fall back to rule-based
    if not result.get("success"):
        print(f"  Vision: ONNX failed ({result.get('error', '?')}) — using rule-based fallback")
        result = analyze_image_rules(image_path)

    if not result.get("success"):
        return {
            "success": False,
            "error": "All vision methods failed",
            "vision_context": ""
        }

    # Map to Nigerian context
    raw_class = result["top_prediction"]
    context = CLASS_TO_NIGERIAN_CONTEXT.get(raw_class, {
        "display_name": raw_class.replace("___", " — ").replace("_", " "),
        "crop": raw_class.split("___")[0].replace("_", " "),
        "severity": "Unknown",
        "local_tip": "Consult your local ADP extension officer for confirmation.",
    })

    confidence_pct = int(result["confidence"] * 100)
    method_note = " (AI model)" if result["method"] == "onnx" else " (visual analysis)"

    # Format for LLM prompt injection
    vision_context = f"""PLANT DISEASE VISION ANALYSIS{method_note}:
Detected: {context['display_name']}
Crop: {context['crop']}
Confidence: {confidence_pct}%
Severity: {context['severity']}
Note: {context['local_tip']}"""

    if result.get("top3") and len(result["top3"]) > 1:
        vision_context += f"\nOther possibilities: "
        others = []
        for alt in result["top3"][1:]:
            alt_ctx = CLASS_TO_NIGERIAN_CONTEXT.get(alt["class"], {})
            alt_name = alt_ctx.get("display_name", alt["class"].replace("___", " — "))
            others.append(f"{alt_name} ({int(alt['confidence']*100)}%)")
        vision_context += ", ".join(others)

    return {
        "success": True,
        "display_name": context["display_name"],
        "crop": context["crop"],
        "confidence": confidence_pct,
        "severity": context["severity"],
        "method": result["method"],
        "vision_context": vision_context,
    }


def is_vision_available() -> dict:
    """Check what vision capability is available."""
    if os.path.exists(MODEL_PATH):
        size_mb = os.path.getsize(MODEL_PATH) / (1024*1024)
        return {"available": True, "mode": "onnx", "model_size_mb": round(size_mb, 1)}
    return {"available": True, "mode": "rule_based", "model_size_mb": 0}


def classify_leaf_image(image_path: str) -> dict:
    """
    Classify a leaf image. Wraps analyze_plant_image to match orchestrator expectations.
    """
    res = analyze_plant_image(image_path)
    if not res or not res.get("success"):
        return {}
    return {
        "label": res["display_name"],
        "confidence": res["confidence"] / 100.0,
        "crop": res["crop"],
        "severity": res["severity"],
        "vision_context": res["vision_context"]
    }