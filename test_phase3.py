
import sys
import io
sys.path.insert(0, '.')
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from src.rag import retrieve_context

# Test 1: Symptom query
print('=== TEST 1: Symptom query ===')
print(retrieve_context('my maize leaves have holes and sawdust inside'))

print()

# Test 2: Market query
print('=== TEST 2: Market query ===')
print(retrieve_context('how much can I sell my tomatoes for in Lagos'))

print()

# Test 3: Pidgin-style query
print('=== TEST 3: Pidgin query ===')
print(retrieve_context('my cassava leaves dey yellow with green patches'))
