
from src.database import get_full_crop_context, search_pests_by_symptom
print(get_full_crop_context('cassava'))

results = search_pests_by_symptom('yellow leaves')
for p in results:
    print(p['name'], '|', p['severity'])
