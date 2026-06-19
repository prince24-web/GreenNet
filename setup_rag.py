"""
setup_rag.py — populate ChromaDB with agronomic knowledge documents.
Run once after setup_db.py.
"""
import sys
sys.path.insert(0, '.')

from src.rag import add_document, get_collection_stats
from src.database import get_all_crops, get_pests_for_crop, get_treatments_for_pest, get_full_crop_context


def build_crop_documents():
    """Create one rich document per crop and index it."""
    print("  Indexing crop knowledge...")
    crops = get_all_crops()

    for crop in crops:
        doc_id = f"crop_{crop['id']}_{crop['name'].lower().replace(' ', '_')}"
        text = get_full_crop_context(crop['name'])

        if text:
            add_document(
                doc_id=doc_id,
                text=text,
                metadata={
                    "source": "AgriSense Crop Database",
                    "category": "crop_profile",
                    "crop": crop['name'],
                    "zones": crop.get('growing_zones', '')
                }
            )
            print(f"    ✓ {crop['name']}")


def build_pest_documents():
    """Create focused pest + symptom documents for better symptom-based retrieval."""
    print("  Indexing pest & disease knowledge...")

    pest_docs = [
        {
            "id": "pest_cassava_mosaic",
            "text": """Cassava Mosaic Disease is the most destructive cassava disease in Nigeria.
Symptoms: Yellow and green mosaic pattern on leaves, leaf distortion and curling, severe stunting,
reduced tuber size and yield. Caused by a virus spread by whitefly insects.
Affected crop: Cassava (Akpu, Ege, Rogo).
Severity: High. Can cause up to 80% yield loss.
Treatment: No chemical cure. Plant CMD-resistant varieties like TME 419 from IITA.
Remove and burn infected plants immediately before whiteflies spread the virus.
Cost: Resistant cuttings cost ₦800-1,500 per bundle from IITA offices.""",
            "metadata": {"source": "IITA Nigeria", "category": "disease", "crop": "Cassava"}
        },
        {
            "id": "pest_fall_armyworm",
            "text": """Fall Armyworm (Spodoptera frugiperda) is the most serious maize pest in Nigeria since 2016.
Symptoms: Ragged holes in leaves, sawdust-like frass (droppings) in the whorl of the plant,
entire plant stripped in severe cases. Look inside the whorl — you will find the caterpillar.
Affected crops: Maize (Agbado), Sorghum (Dawa), Millet (Gero).
Season: Rainy season May-September. Most severe June-August.
Severity: Very High — can destroy entire field in days.
Treatment options:
1. Emamectin benzoate (Coragen/Ampligo) — 0.4ml per litre, spray into whorl. Cost ₦1,500-2,500 per 100ml.
2. Chlorpyrifos (Dursban) — 2ml per litre. Cost ₦600-1,000 per 100ml. 
3. Emergency: pour wood ash or sand into whorl — free and works short-term.
Spray early morning. Repeat after 7 days.""",
            "metadata": {"source": "FMARD Nigeria", "category": "pest", "crop": "Maize"}
        },
        {
            "id": "pest_tomato_blight",
            "text": """Late Blight (Phytophthora infestans) is the deadliest tomato disease in Nigeria.
Symptoms: Dark water-soaked lesions on leaves, white fuzzy mold on leaf undersides,
rapid browning and death of entire plant, fruit rots from the stalk end.
Spreads very fast in humid rainy conditions. Can destroy a field in 1 week.
Affected crops: Tomato (Tomati), Pepper.
Season: Rainy season and humid conditions.
Severity: Very High — total crop loss possible without treatment.
Treatment:
1. Ridomil Gold (Metalaxyl + Mancozeb) — 2.5g per litre, spray every 7 days. Cost ₦1,800-3,000 per 100g.
2. Copper Oxychloride (Funguran) — 3g per litre, cheaper alternative. Cost ₦800-1,500 per kg.
Prevention: Avoid overhead irrigation. Space plants for airflow. Remove and burn infected material.""",
            "metadata": {"source": "AgriSense KB", "category": "disease", "crop": "Tomato"}
        },
        {
            "id": "pest_striga_weed",
            "text": """Striga (witchweed, Kakariya) is a parasitic weed that attaches to crop roots underground.
By the time it appears above ground, it has already stolen nutrients for weeks.
Symptoms: Stunted yellow crop plants, wilting despite adequate rain, small purple-pink flowering
weed plants emerging from soil near crop stems.
Affected crops: Sorghum, Maize, Millet, Cowpea — especially in northern Nigeria.
Severity: Very High — can cause 20-80% yield loss. Seeds persist in soil 20+ years.
Treatment:
1. IR Maize (Imazapyr Resistant) seed — Striga dies on contact with treated roots. 
   Cost ₦1,000-2,000/kg. Available from IITA and NASC.
2. Hand pull Striga before it flowers — MUST be before seed set or problem worsens.
   Burn pulled plants — never compost.
3. Crop rotation with groundnut or soybean reduces Striga population over time.""",
            "metadata": {"source": "IITA Nigeria", "category": "weed", "crop": "Sorghum/Maize"}
        },
        {
            "id": "pest_groundnut_rosette",
            "text": """Groundnut Rosette Virus is the most devastating groundnut disease in Nigeria.
Symptoms: Severe stunting, leaves become very small and chlorotic (yellow-green),
bushy appearance, plants stop producing pods. Total crop failure possible.
Spread by aphid insects (Aphis craccivora).
Affected crop: Groundnut (Epa, Gyada).
Severity: Very High — can cause 100% crop failure in late-planted crops.
Treatment: No chemical cure for the virus itself.
1. Plant early (May) before aphid populations peak.
2. Use resistant varieties: Samnut 24, ICGV-IS from NASC or IITA Kano.
3. Control aphid vector: Imidacloprid (Confidor) 0.5ml/L spray. Cost ₦2,000-3,000 per 100ml.
Roguing: Remove infected plants early to prevent spread.""",
            "metadata": {"source": "IITA Nigeria", "category": "disease", "crop": "Groundnut"}
        },
        {
            "id": "pest_locust",
            "text": """Desert Locust (Fara, Eéṣú) swarms are catastrophic agricultural emergencies.
Symptoms: Complete defoliation — entire fields stripped bare within hours.
Only bare stalks remain. Swarms can cover hundreds of hectares.
Affected crops: All crops — maize, sorghum, millet, rice, groundnut, cowpea.
Season: Dry season — harmattan period (November-March).
Severity: Catastrophic — total field loss. Individual control is impossible.
Action: DO NOT attempt individual control — it is futile.
IMMEDIATELY report to:
- State Ministry of Agriculture emergency line
- FMARD Federal Locust Control Unit
- Local Agricultural Development Programme (ADP) office
Government handles aerial malathion ULV spraying.
Early reporting saves neighbouring farms.""",
            "metadata": {"source": "FMARD Nigeria", "category": "pest", "crop": "All crops"}
        },
    ]

    for doc in pest_docs:
        add_document(doc['id'], doc['text'], doc['metadata'])
        print(f"    ✓ {doc['id']}")


def build_practice_documents():
    """Index general best-practice advisory documents."""
    print("  Indexing farming practices...")

    practice_docs = [
        {
            "id": "practice_soil_prep",
            "text": """Soil Preparation Best Practices for Nigerian Smallholder Farmers:
Good soil preparation is the foundation of a good harvest. Steps:
1. Clear land: Remove crop residue and weeds 3-4 weeks before planting.
2. Plough or ridge: Till soil to 20-30cm depth. Ridge for yam and cassava.
3. Soil test: Ideal pH for most Nigerian crops is 5.5-6.5. If soil is too acidic, apply
   agricultural lime — 1-2 tonnes per hectare. Cost ₦15,000-25,000 per tonne.
4. Add organic matter: Compost or poultry manure — 5-10 tonnes per hectare.
   Poultry manure costs ₦8,000-12,000 per tonne. Improves water retention and nutrients.
5. Mark rows: Use correct spacing — maize 75x25cm, tomato 60x60cm, yam 1mx1m.
Planting into well-prepared soil increases yield by 30-50% compared to unprepared land.""",
            "metadata": {"source": "AgriSense KB", "category": "practice", "crop": "General"}
        },
        {
            "id": "practice_irrigation",
            "text": """Irrigation Management for Dry Season Farming in Nigeria:
Dry season farming is highly profitable but requires water management.
Options for smallholder farmers:
1. Drip irrigation: Most efficient — 30-50% less water than flooding.
   Cost: ₦150,000-300,000 per hectare to install. Lasts 5-7 years.
2. Sprinkler: Good for vegetables. Cost ₦80,000-150,000 per hectare.
3. Manual watering: Buckets or watering cans — cheap but labour intensive.
   Suitable for small plots under 0.5 hectare.
4. Pump from river/borehole: Petrol pump costs ₦80,000-150,000.
   Daily petrol cost ₦2,000-5,000 depending on field size.
Water timing: Irrigate early morning (5-8am) or evening (5-7pm).
Avoid midday — high evaporation loss. Most crops need 25-50mm water per week.""",
            "metadata": {"source": "AgriSense KB", "category": "practice", "crop": "General"}
        },
        {
            "id": "practice_post_harvest",
            "text": """Post-Harvest Handling to Reduce Losses for Nigerian Farmers:
Nigeria loses 40-50% of produce to post-harvest problems. Key steps:
Cassava: Process within 24-48 hours of harvest — cassava deteriorates very fast.
Make garri, fufu, or starch. Dried garri stores 6-12 months.
Maize: Dry to below 13% moisture before storing. Use hermetic bags (PICS bags) to
prevent weevil damage. Cost ₦800-1,200 per bag. Stores 6-12 months safely.
Tomato: Harvest before fully ripe for transport. Sell within 3-5 days or process to paste.
Tomato paste processing: cook, blend, boil, seal in jars. Extends shelf life 12 months.
Yam: Store in yam barn — cool, dark, with good airflow. Lasts 4-6 months.
Rice: Thresh, winnow, dry, mill, bag in hermetic bags. Store in cool dry place.
Market timing: Prices are lowest at harvest. Store and sell 2-3 months later for 30-60% premium.""",
            "metadata": {"source": "AgriSense KB", "category": "post_harvest", "crop": "General"}
        },
        {
            "id": "practice_intercropping",
            "text": """Intercropping Systems for Nigerian Smallholder Farmers:
Intercropping — growing two crops together — increases total income per hectare.
Best combinations:
1. Maize + Cowpea: Maize provides shade for cowpea, cowpea fixes nitrogen for maize.
   Plant cowpea 2-3 weeks after maize. Increases combined income by 30-40%.
2. Cassava + Maize: Maize harvested at 3 months, cassava continues to 12-18 months.
   Income in first season while cassava matures.
3. Yam + Melon (Egusi): Egusi planted between yam rows. Extra income from same land.
4. Sorghum + Cowpea (north Nigeria): Traditional and productive combination.
5. Plantain + Cocoa: Long-term system — plantain provides shade for young cocoa.
Benefits: Better land use, reduced pest pressure, income throughout the year.
Avoid: Do not intercrop tomato with other crops — disease spreads between them.""",
            "metadata": {"source": "AgriSense KB", "category": "practice", "crop": "General"}
        },
        {
            "id": "practice_market",
            "text": """Market Strategy and Price Negotiation for Nigerian Farmers:
Getting better prices is as important as growing a good crop.
Key strategies:
1. Form a cooperative: Sell together with other farmers — larger volume = better price.
   Cooperatives can negotiate 15-25% above individual farmer prices.
2. Avoid distress selling: Do not sell immediately after harvest when prices are lowest.
   Store (using hermetic bags or cold room) and sell 4-8 weeks later.
3. Know your price: Check Dawanau market (Kano), Mile 12 (Lagos), Bodija (Ibadan) prices
   before selling to middlemen. Middlemen typically pay 30-40% below market price.
4. Process before selling: Garri from cassava, dried pepper, tomato paste, groundnut oil —
   processed products sell for 2-4x the raw commodity price.
5. Target institutional buyers: School feeding programs, hospitals, food companies.
   They buy in bulk at fair prices consistently.
6. Transport collectively: Share truck costs to reduce per-bag transport cost by 50%.""",
            "metadata": {"source": "AgriSense KB", "category": "market", "crop": "General"}
        },
    ]

    for doc in practice_docs:
        add_document(doc['id'], doc['text'], doc['metadata'])
        print(f"    ✓ {doc['id']}")


def main():
    print("Building AgriSense RAG knowledge base...\n")

    build_crop_documents()
    print()
    build_pest_documents()
    print()
    build_practice_documents()

    stats = get_collection_stats()
    print(f"\n✓ ChromaDB populated: {stats['total_documents']} documents indexed")
    print("✓ Phase 3 complete. Ready for Phase 4 — vision module.")


if __name__ == "__main__":
    main()