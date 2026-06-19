import requests
import json

OLLAMA_BASE_URL = "http://localhost:11434"
LLM_MODEL = "qwen2.5:1.5b"
EMBED_MODEL = "nomic-embed-text"


def chat(prompt: str, system: str = None) -> str:
    """Send a prompt to Qwen2.5 and return the response text."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": LLM_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.3,      # low = more factual, good for agriculture
            "num_ctx": 2048,         # context window — keep low for Pentium Silver
            "num_predict": 512,      # max tokens to generate
        }
    }

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json=payload,
            timeout=120
        )
        response.raise_for_status()
        return response.json()["message"]["content"]
    except requests.exceptions.ConnectionError:
        return "Error: Ollama is not running. Please start it with: ollama serve"
    except Exception as e:
        return f"Error: {str(e)}"


def embed(text: str) -> list[float]:
    """Get an embedding vector for a piece of text."""
    payload = {
        "model": EMBED_MODEL,
        "prompt": text
    }

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            json=payload,
            timeout=120
        )
        response.raise_for_status()
        return response.json()["embedding"]
    except Exception as e:
        print(f"Embedding error: {e}")
        return []


def is_ollama_running() -> bool:
    """Quick health check before the app starts."""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False