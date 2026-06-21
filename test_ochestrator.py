import sys
import io
sys.path.insert(0, '.')
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from src.orchestrator import handle_query

print("=== Orchestrator Test ===\n")

# Test 1: Plain text query, no image
#result = handle_query("My maize leaves are turning yellow, what should I do?")
#print("Test 1 — text only:")
#print(result["answer"])
#print(f"(had_context: {result['had_context']})\n")

# Test 2: With an image (use a real test image path once Phase 4 model is ready)
result = handle_query("What's wrong with my cassava?", image_path="data\test_images\content_WhatsApp_Image_2021-05-10_at_5.54.59_AM_(1).jpeg")
print("Test 2 — with image:")
print(result["answer"])
print(f"Vision result: {result['vision_result']}\n")

print("=== Test complete ===")
