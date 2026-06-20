import sys
sys.path.insert(0, '.')

from src.orchestrator import handle_query

print("=== Orchestrator Test ===\n")

# Test 1: Plain text query, no image
result = handle_query("My maize leaves are turning yellow, what should I do?")
print("Test 1 — text only:")
print(result["answer"])
print(f"(had_context: {result['had_context']})\n")

# Test 2: With an image (use a real test image path once Phase 4 model is ready)
# result = handle_query("What's wrong with my cassava?", image_path="data/test_images/sample_leaf.jpg")
# print("Test 2 — with image:")
# print(result["answer"])
# print(f"Vision result: {result['vision_result']}\n")

print("=== Test complete ===")