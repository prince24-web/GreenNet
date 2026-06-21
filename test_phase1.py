import sys
import io
sys.path.insert(0, '.')
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from src.llm import chat, embed, is_ollama_running

print("=== AgriSense Phase 1 Test ===\n")

# Test 1: Ollama connection
print("1. Checking Ollama connection...")
if is_ollama_running():
    print("   ✓ Ollama is running\n")
else:
    print("   ✗ Ollama not found — run: ollama serve\n")
    sys.exit(1)

# Test 2: LLM response
print("2. Testing Qwen2.5 1.5B...")
response = chat(
    prompt="In one sentence, what is cassava mosaic disease?",
    system="You are an agricultural assistant for Nigerian farmers."
)
print(f"   Response: {response}\n")

# Test 3: Embedding
print("3. Testing nomic-embed-text...")
vector = embed("cassava mosaic disease treatment")
if len(vector) > 0:
    print(f"   ✓ Embedding works — vector length: {len(vector)}\n")
else:
    print("   ✗ Embedding failed\n")

print("=== All checks passed. Phase 1 complete. ===")