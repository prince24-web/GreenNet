import sqlite3
import os

DB_PATH = os.path.join('data', 'agrisense.db')

def create_tables(cur):
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS crops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            local_names TEXT,
            growing_zones TEXT,
            planting_months TEXT,
            harvest_months TEXT,
            soil_type TEXT,
            water_needs TEXT,
            yield_per_hectare TEXT,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS pests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            local_name TEXT,
            type TEXT,
            affected_crops TEXT,
            symptoms TEXT,
            severity TEXT,
            season TEXT
        );

        CREATE TABLE IF NOT EXISTS treatments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pest_id INTEGER,
            method TEXT,
            product_name TEXT,
            product_detail TEXT,
            dosage TEXT,
            cost_naira TEXT,
            availability TEXT,
            notes TEXT,
            FOREIGN KEY (pest_id) REFERENCES pests(id)
        );

        CREATE TABLE IF NOT EXISTS fertilizers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crop_id INTEGER,
            fertilizer_name TEXT,
            npk_ratio TEXT,
            application_stage TEXT,
            kg_per_hectare TEXT,
            cost_naira_per_bag TEXT,
            timing_weeks TEXT,
            FOREIGN KEY (crop_id) REFERENCES crops(id)
        );

        CREATE TABLE IF NOT EXISTS market_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crop_id INTEGER,
            region TEXT,
            price_per_kg_naira REAL,
            price_per_bag_naira REAL,
            market_name TEXT,
            last_updated TEXT,
            trend TEXT,
            FOREIGN KEY (crop_id) REFERENCES crops(id)
        );
    """)


def seed_crops(cur):
    crops = [
        ("Cassava", "Akpu, Ege, Rogo, Gbaguda",
         "South-South, South-East, South-West, North-Central",
         "March-April, September-October", "12-18 months after planting",
         "Sandy loam, well-drained", "Low to moderate — drought tolerant",
         "10-25 tonnes/ha", "Most widely grown crop in Nigeria. Versatile: garri, fufu, starch."),

        ("Maize", "Agbado, Masara, Oka",
         "All zones — best in derived savanna",
         "March-April (first season), July-August (second season)",
         "90-120 days after planting",
         "Well-drained loamy soil", "Moderate — needs 500-800mm rainfall",
         "2-4 tonnes/ha", "Staple food and animal feed. Two seasons per year possible."),

        ("Yam", "Ji, Isu, Doya",
         "Middle Belt, South-East, South-West",
         "February-April", "7-9 months after planting",
         "Deep, well-drained loamy soil", "Moderate to high",
         "15-25 tonnes/ha", "High value crop. Requires staking. Store in barn after harvest."),

        ("Tomato", "Tomati, Gauta",
         "Kano, Kaduna, Jos Plateau, South-West",
         "October-January (dry season with irrigation), May-June (rainy)",
         "70-90 days after transplanting",
         "Loamy, slightly acidic pH 5.5-7", "High — needs regular watering",
         "20-30 tonnes/ha", "Very perishable. Sell quickly or process. High market demand year-round."),

        ("Sorghum", "Okababa, Dawa, Oka baba",
         "North-West, North-East, North-Central",
         "May-June", "3-5 months after planting",
         "Sandy loam to clay loam, tolerates poor soil", "Low — highly drought tolerant",
         "1-3 tonnes/ha", "Excellent for dry north. Used for food, feed, and local brewing."),

        ("Groundnut", "Epa, Gyada, Okpa",
         "North-West, North-East, derived savanna",
         "May-July", "90-130 days after planting",
         "Sandy loam, well-drained, pH 5.5-7", "Moderate",
         "1-2 tonnes/ha", "Good for crop rotation — fixes nitrogen. Oil and protein crop."),

        ("Cowpea", "Ewa, Wake, Kunde",
         "All zones — especially the North",
         "May-July (north), March-April (south)", "60-90 days",
         "Sandy loam, tolerates poor soil", "Low — drought tolerant",
         "0.5-1.5 tonnes/ha", "Excellent protein source. Good intercrop with maize or sorghum."),

        ("Rice", "Iresi, Shinkafa, Osikapa",
         "Niger Delta, Kebbi, Ebonyi, Anambra, Benue",
         "May-June (upland), March (lowland irrigated)", "4-6 months",
         "Clay loam, water-retentive for lowland", "High — needs flooded or moist conditions",
         "3-6 tonnes/ha", "Demand exceeds supply in Nigeria. High profit but water-intensive."),

        ("Plantain", "Ogede, Ayaba, Unere",
         "South-South, South-East, South-West",
         "Any time — perennial crop", "12-18 months first harvest, ratoons every 9 months",
         "Rich loamy, well-drained", "High — 1200mm+ rainfall",
         "20-40 tonnes/ha", "Perennial — plant once, harvest for years. Process into chips for longer shelf life."),

        ("Sweet Potato", "Anamo, Dankali-mai-zaki, Edesi",
         "All zones — especially Jos Plateau and South",
         "March-April, August-September", "3-5 months",
         "Sandy loam, well-drained", "Moderate",
         "10-15 tonnes/ha", "Fast growing. Drought tolerant. Good for food security crops."),

        ("Pepper (Hot)", "Tatashe, Bawa, Ose oyibo",
         "South-West, South-East, North-Central",
         "March-April (seedbed), transplant after 4-6 weeks", "90-120 days",
         "Loamy, well-drained, pH 6-7", "Moderate to high",
         "5-10 tonnes/ha", "High value. Dry pepper fetches premium price. Sun-dry after harvest."),

        ("Okra", "Ila, Kubewa, Okwuru",
         "All zones",
         "March-April, July-August", "55-65 days",
         "Loamy, well-drained", "Moderate",
         "5-8 tonnes/ha", "Fast turnaround. Popular in local cuisine. Fresh and dried markets."),

        ("Melon (Egusi)", "Egusi, Agushi",
         "South-West, South-East, North-Central",
         "March-April", "90-120 days",
         "Sandy loam", "Low to moderate",
         "0.8-1.5 tonnes/ha (seed)", "Seeds are the product. High demand in south. Process and bag for shelf life."),

        ("Soybean", "Soya, Wake-anguku",
         "Middle Belt — Benue, Nasarawa, Plateau, Kaduna",
         "June-July", "90-120 days",
         "Loamy, pH 6-7", "Moderate",
         "1-2.5 tonnes/ha", "High protein, high demand from feed mills and food processors."),

        ("Onion", "Alubosa, Albasa",
         "Kebbi, Sokoto, Kano, Niger State (dry season)",
         "October-November (dry season)", "90-120 days",
         "Sandy loam, well-drained", "High — needs irrigation in dry season",
         "15-25 tonnes/ha", "Very high value. Dry season production using irrigation near rivers."),

        ("Banana", "Ogede wewe, Ayaba",
         "South-South, South-West, South-East",
         "Perennial — any time", "9-12 months first bunch",
         "Rich loamy, well-drained", "High",
         "30-50 tonnes/ha", "Similar to plantain. Fresh consumption market. Export potential."),

        ("Watermelon", "Elegede, Kankana",
         "North — Kebbi, Kano, Zamfara, Sokoto",
         "October-January (dry season with irrigation)", "70-90 days",
         "Sandy loam, well-drained", "High — needs irrigation",
         "20-40 tonnes/ha", "High profit in dry season. Sell fast — perishable."),

        ("Cocoa", "Koko, Cocoa",
         "South-West (Ondo, Osun, Oyo), South-East, South-South",
         "April-June", "3-5 years first harvest, perennial",
         "Deep loamy, humid, pH 6-7", "High — needs 1500mm+ rainfall",
         "0.5-1.5 tonnes/ha (dry beans)", "Export crop. Long-term investment. FMARD has subsidy programs."),

        ("Millet (Pearl)", "Gero, Maiwa",
         "North-West, North-East — dry arid zones",
         "June-July", "60-90 days",
         "Sandy, poor soil — very tolerant", "Very low — drought resistant",
         "0.5-1 tonne/ha", "Survives where others fail. Staple in far north. Food security crop."),

        ("Ginger", "Citta, Jinja",
         "Kaduna, Nassarawa, Benue, Gombe",
         "April-May", "8-10 months",
         "Sandy loam, rich organic matter", "Moderate to high",
         "10-20 tonnes/ha (fresh)", "Nigeria is world's largest ginger exporter. High export value."),
    ]

    cur.executemany("""
        INSERT INTO crops (name, local_names, growing_zones, planting_months,
                           harvest_months, soil_type, water_needs, yield_per_hectare, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, crops)


def seed_pests(cur):
    pests = [
        ("Cassava Mosaic Disease", "Arun cassava", "Viral disease",
         "Cassava",
         "Yellow and green mosaic pattern on leaves, leaf distortion, stunted growth, reduced tuber size",
         "High", "Year-round, worse in dry season"),

        ("Cassava Mealybug", "Udele cassava", "Insect pest",
         "Cassava",
         "White cottony masses on stems and undersides of leaves, yellowing, wilting, sooty mold",
         "High", "Dry season"),

        ("Fall Armyworm", "Kokoro agbado, Tsutsuma", "Insect pest",
         "Maize, Sorghum, Millet",
         "Ragged holes in leaves, sawdust-like frass in whorl, entire plant defoliation in severe cases",
         "Very High", "Rainy season May-September"),

        ("Maize Streak Virus", "Arun agbado", "Viral disease",
         "Maize",
         "Yellow streaks running length of leaf, stunting, poor cob formation",
         "High", "Rainy season"),

        ("Tomato Blight (Late)", "Arun tomati", "Fungal disease",
         "Tomato, Pepper",
         "Dark water-soaked lesions on leaves, white mold on leaf undersides, fruit rot, rapid plant death",
         "Very High", "Rainy season, high humidity"),

        ("Tomato Leaf Miner", "Kokoro tomati", "Insect pest",
         "Tomato",
         "Winding white mines/trails on leaves, leaf drying, reduced photosynthesis",
         "Medium", "Dry season"),

        ("Yam Beetle", "Kokoro isu", "Insect pest",
         "Yam",
         "Holes bored into tubers, rotting from entry wounds, yield loss at harvest",
         "High", "Late rainy season"),

        ("Groundnut Rosette Virus", "Arun epa", "Viral disease",
         "Groundnut",
         "Severe stunting, small chlorotic leaves, bushy appearance, total crop failure possible",
         "Very High", "Rainy season"),

        ("Rice Yellow Mottle Virus", "Arun shinkafa", "Viral disease",
         "Rice",
         "Yellow streaks on leaves, stunting, empty grains, up to 100% yield loss",
         "Very High", "Rainy season"),

        ("Sorghum Striga", "Kakariya, Witch weed", "Parasitic weed",
         "Sorghum, Maize, Millet, Cowpea",
         "Stunted yellow plants, wilting despite rain, purple-pink flowering weed emerging from soil near roots",
         "Very High", "Rainy season"),

        ("Pepper Thrips", "Kokoro ose", "Insect pest",
         "Pepper, Tomato, Onion",
         "Silver streaks on leaves, distorted young leaves, scarred fruits, flower drop",
         "Medium", "Dry season"),

        ("Cowpea Aphid", "Kokoro ewa", "Insect pest",
         "Cowpea, Groundnut",
         "Clusters of small green/black insects on growing tips, yellowing, honeydew, sooty mold",
         "Medium", "Dry season and early rains"),

        ("Banana/Plantain Black Sigatoka", "Arun ogede", "Fungal disease",
         "Plantain, Banana",
         "Dark brown-black streaks on leaves expanding to large necrotic areas, premature fruit ripening",
         "High", "Rainy season, high humidity"),

        ("Onion Downy Mildew", "Arun alubosa", "Fungal disease",
         "Onion",
         "Pale green to yellow patches on leaves, gray-purple fuzzy growth, leaf collapse",
         "High", "Cool humid conditions"),

        ("Locust (Desert)", "Eéṣú, Fara", "Insect pest",
         "Maize, Sorghum, Millet, Rice, Cowpea, Groundnut",
         "Complete defoliation of entire fields within hours, bare stalks remaining",
         "Catastrophic", "Dry season — harmattan period"),
    ]

    cur.executemany("""
        INSERT INTO pests (name, local_name, type, affected_crops, symptoms, severity, season)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, pests)


def seed_treatments(cur):
    # Get pest IDs — order matches seed_pests above
    treatments = [
        # Cassava Mosaic Disease (pest_id=1)
        (1, "Cultural", "Use CMD-resistant varieties (TME 419, IITA TMS)",
         "Resistant cassava cuttings from IITA or NASC",
         "Plant entire field with resistant variety",
         "₦800-1,500 per bundle of cuttings",
         "IITA offices, certified seed sellers", "Most effective long-term solution"),

        (1, "Cultural", "Rogue out infected plants",
         "No product — manual removal",
         "Remove and burn infected plants within 2 weeks of detection",
         "Free — labour cost only",
         "Anywhere", "Remove before whitefly spreads virus further"),

        # Cassava Mealybug (pest_id=2)
        (2, "Chemical", "Dimethoate 40% EC",
         "Dimethoate (Rogor, Dimate)", "2ml per litre of water, spray undersides of leaves",
         "₦800-1,200 per 100ml", "Agro shops nationwide",
         "Spray in cool morning hours. Wear gloves."),

        (2, "Biological", "Introduce natural predator Anagyrus lopezi",
         "Biocontrol agents from IITA Ibadan",
         "Release 200-500 wasps per hectare",
         "Contact IITA — often free for smallholders",
         "IITA Ibadan", "Sustainable long-term control"),

        # Fall Armyworm (pest_id=3)
        (3, "Chemical", "Emamectin benzoate 1.9% EC",
         "Coragen, Ampligo, Match", "0.4ml per litre, spray into whorl of plant",
         "₦1,500-2,500 per 100ml", "Major agro dealers",
         "Spray early morning. Repeat after 7 days if infestation severe."),

        (3, "Cultural", "Apply sand or ash into whorl",
         "Wood ash or fine sand", "1 teaspoon per plant whorl",
         "Free if ash available", "Anywhere",
         "Emergency cheap measure. Disrupts larvae feeding."),

        (3, "Chemical", "Chlorpyrifos 48% EC",
         "Pyrifos, Dursban", "2ml per litre of water",
         "₦600-1,000 per 100ml", "Agro shops",
         "Do not apply within 2 weeks of harvest."),

        # Maize Streak Virus (pest_id=4)
        (4, "Cultural", "Plant streak-resistant varieties",
         "IITA open-pollinated varieties — SUWAN 1, TZSRW",
         "Replace susceptible varieties entirely",
         "₦500-800 per kg seed", "NASC, IITA, certified dealers",
         "Leafhopper insect spreads this virus — control vectors too"),

        (4, "Chemical", "Control leafhopper vector with Imidacloprid",
         "Confidor, Gaucho", "Seed treatment or 0.5ml/L foliar spray",
         "₦2,000-3,000 per 100ml", "Agro shops",
         "Treat seeds before planting for best protection"),

        # Tomato Late Blight (pest_id=5)
        (5, "Chemical", "Metalaxyl + Mancozeb",
         "Ridomil Gold, Mancolaxyl", "2.5g per litre of water",
         "₦1,800-3,000 per 100g", "Major agro shops",
         "Preventive spraying before rains. Alternate with copper fungicide."),

        (5, "Chemical", "Copper Oxychloride",
         "Funguran, Cuprofix", "3g per litre of water",
         "₦800-1,500 per kg", "Agro shops nationwide",
         "Spray every 7-10 days during humid periods"),

        # Tomato Leaf Miner (pest_id=6)
        (6, "Chemical", "Abamectin 1.8% EC",
         "Dynamec, Vertimec", "1ml per litre of water",
         "₦1,200-2,000 per 100ml", "Major agro dealers",
         "Spray when mines first appear. Rotate chemicals to prevent resistance."),

        # Yam Beetle (pest_id=7)
        (7, "Chemical", "Carbofuran 3% granules",
         "Furadan (use with care — toxic)", "1kg per plot at planting",
         "₦600-900 per kg", "Agro shops",
         "Apply at planting only. Do not handle with bare hands. Very toxic."),

        (7, "Cultural", "Harvest on time — do not leave in ground",
         "No product", "Harvest when vines die back — do not delay",
         "Free", "Anywhere",
         "Delayed harvest increases beetle damage significantly"),

        # Groundnut Rosette (pest_id=8)
        (8, "Cultural", "Early planting — May to avoid peak aphid flight",
         "Resistant variety: Samnut 24, ICGV-IS",
         "Plant early in season before aphid populations build",
         "₦600-1,000 per kg seed", "NASC, IITA Kano office",
         "Virus spreads by aphids — early planting avoids peak vector season"),

        # Rice Yellow Mottle (pest_id=9)
        (9, "Cultural", "Use FARO resistant varieties",
         "FARO 44, FARO 52, FARO 60 — WARDA/AfricaRice varieties",
         "Replace entire planting with resistant variety",
         "₦600-1,200 per kg", "NASC, RIFAN offices",
         "No chemical cure — resistance is only effective strategy"),

        # Striga (pest_id=10)
        (10, "Chemical", "Imazapyr herbicide seed coating",
         "IR Maize / Striga-tolerant seed (Imazapyr Resistant varieties)",
         "Use pre-treated IR maize seed — Striga dies on contact with roots",
         "₦1,000-2,000 per kg treated seed", "IITA, NASC",
         "Most effective Striga control available to smallholders"),

        (10, "Cultural", "Hand pull Striga before it flowers",
         "No product — manual labour",
         "Pull and burn Striga plants before flowering — do not compost",
         "Free — labour intensive", "Anywhere",
         "Must pull before seed set or you worsen next season's problem"),

        # Pepper Thrips (pest_id=11)
        (11, "Chemical", "Spinosad 45% SC",
         "Tracer, Entrust", "0.5ml per litre",
         "₦3,000-5,000 per 100ml", "Major agro dealers",
         "Very effective. Low mammalian toxicity. Spray in evenings."),

        # Cowpea Aphid (pest_id=12)
        (12, "Chemical", "Pymetrozine or Imidacloprid",
         "Chess, Confidor", "0.5ml per litre",
         "₦1,500-2,500 per 100ml", "Agro shops",
         "Spray growing tips where aphids cluster"),

        (12, "Cultural", "Intercrop with maize or sorghum",
         "No product", "Plant cowpea between maize rows",
         "Free", "Anywhere",
         "Physical barrier disrupts aphid spread"),

        # Black Sigatoka (pest_id=13)
        (13, "Chemical", "Mancozeb 80% WP",
         "Dithane M-45, Mancozeb", "2.5g per litre, spray leaves thoroughly",
         "₦800-1,200 per kg", "Agro shops nationwide",
         "Spray every 14 days during rainy season"),

        # Onion Downy Mildew (pest_id=14)
        (14, "Chemical", "Metalaxyl + Mancozeb",
         "Ridomil Gold", "2g per litre",
         "₦1,800-3,000 per 100g", "Major agro shops",
         "Begin spraying preventively 3 weeks after transplanting"),

        # Locust (pest_id=15)
        (15, "Report to authority", "Contact State Ministry of Agriculture immediately",
         "Government vector control — malathion ULV aerial spray",
         "Report sighting — do not attempt individual control",
         "Government handles cost", "State Ministry of Agriculture, FMARD hotline",
         "Individual farmers cannot control locusts. Collective early reporting is the only action."),
    ]

    cur.executemany("""
        INSERT INTO treatments (pest_id, method, product_name, product_detail, dosage, cost_naira, availability, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, treatments)


def seed_fertilizers(cur):
    fertilizers = [
        # Cassava (crop_id=1)
        (1, "NPK 12-12-17", "12-12-17", "Basal application", "400", "₦22,000-25,000", "4-6"),
        (1, "Urea", "46-0-0", "Top dressing", "150", "₦18,000-22,000", "8-10"),

        # Maize (crop_id=2)
        (2, "NPK 15-15-15", "15-15-15", "Basal — at planting", "250", "₦22,000-26,000", "1-2"),
        (2, "Urea", "46-0-0", "Top dressing", "150", "₦18,000-22,000", "4-5"),
        (2, "Urea", "46-0-0", "Second top dressing", "100", "₦18,000-22,000", "7-8"),

        # Yam (crop_id=3)
        (3, "NPK 15-15-15", "15-15-15", "Basal", "300", "₦22,000-26,000", "4"),
        (3, "Sulphate of Ammonia", "21-0-0", "Top dressing", "200", "₦14,000-18,000", "10"),

        # Tomato (crop_id=4)
        (4, "NPK 15-15-15", "15-15-15", "At transplanting", "200", "₦22,000-26,000", "1"),
        (4, "CAN (Calcium Ammonium Nitrate)", "26-0-0", "Top dressing", "150", "₦16,000-20,000", "4"),
        (4, "NPK 20-10-10", "20-10-10", "Fruiting stage", "100", "₦24,000-28,000", "7"),

        # Sorghum (crop_id=5)
        (5, "NPK 15-15-15", "15-15-15", "Basal", "200", "₦22,000-26,000", "2"),
        (5, "Urea", "46-0-0", "Top dressing", "100", "₦18,000-22,000", "5"),

        # Rice (crop_id=8)
        (8, "NPK 15-15-15", "15-15-15", "Basal at transplanting", "300", "₦22,000-26,000", "1"),
        (8, "Urea", "46-0-0", "Tillering stage", "150", "₦18,000-22,000", "5"),
        (8, "Urea", "46-0-0", "Panicle initiation", "100", "₦18,000-22,000", "9"),

        # Onion (crop_id=15)
        (15, "NPK 15-15-15", "15-15-15", "Basal", "300", "₦22,000-26,000", "1-2"),
        (15, "Urea", "46-0-0", "Top dressing", "150", "₦18,000-22,000", "4"),
        (15, "Muriate of Potash", "0-0-60", "Bulb development", "100", "₦20,000-24,000", "7"),
    ]

    cur.executemany("""
        INSERT INTO fertilizers (crop_id, fertilizer_name, npk_ratio, application_stage,
                                  kg_per_hectare, cost_naira_per_bag, timing_weeks)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, fertilizers)


def seed_market_prices(cur):
    prices = [
        # Cassava (crop_id=1)
        (1, "Lagos", 85.0, 4250.0, "Mile 12 Market", "2024-11", "Rising"),
        (1, "Onitsha", 70.0, 3500.0, "Ose Market", "2024-11", "Stable"),
        (1, "Ibadan", 75.0, 3750.0, "Bodija Market", "2024-11", "Rising"),

        # Maize (crop_id=2)
        (2, "Kano", 280.0, 14000.0, "Dawanau Grain Market", "2024-11", "Rising"),
        (2, "Lagos", 320.0, 16000.0, "Mile 12 Market", "2024-11", "Rising"),
        (2, "Onitsha", 300.0, 15000.0, "Ose Market", "2024-11", "Stable"),

        # Yam (crop_id=3)
        (3, "Lagos", 500.0, 25000.0, "Mile 12 Market", "2024-11", "Stable"),
        (3, "Onitsha", 420.0, 21000.0, "Ose Market", "2024-11", "Falling"),
        (3, "Abuja", 550.0, 27500.0, "Wuse Market", "2024-11", "Rising"),

        # Tomato (crop_id=4)
        (4, "Kano", 350.0, 8750.0, "Rimi Market", "2024-11", "Falling"),
        (4, "Lagos", 600.0, 15000.0, "Mile 12 Market", "2024-11", "Rising"),
        (4, "Ibadan", 400.0, 10000.0, "Bodija Market", "2024-11", "Stable"),

        # Rice (crop_id=8)
        (8, "Kebbi", 550.0, 27500.0, "Argungu Market", "2024-11", "Stable"),
        (8, "Lagos", 750.0, 37500.0, "Mile 12 Market", "2024-11", "Rising"),
        (8, "Abuja", 700.0, 35000.0, "Wuse Market", "2024-11", "Rising"),

        # Groundnut (crop_id=6)
        (6, "Kano", 700.0, 35000.0, "Dawanau Market", "2024-11", "Rising"),
        (6, "Abuja", 800.0, 40000.0, "Wuse Market", "2024-11", "Rising"),

        # Onion (crop_id=15)
        (15, "Sokoto", 400.0, 20000.0, "Sokoto Market", "2024-11", "Falling"),
        (15, "Lagos", 700.0, 35000.0, "Mile 12 Market", "2024-11", "Rising"),
        (15, "Kano", 450.0, 22500.0, "Rimi Market", "2024-11", "Stable"),

        # Ginger (crop_id=20)
        (20, "Kaduna", 900.0, 45000.0, "Kaduna Central Market", "2024-11", "Rising"),
        (20, "Lagos", 1200.0, 60000.0, "Mile 12 Market", "2024-11", "Rising"),
    ]

    cur.executemany("""
        INSERT INTO market_prices (crop_id, region, price_per_kg_naira, price_per_bag_naira,
                                    market_name, last_updated, trend)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, prices)


def main():
    os.makedirs('data', exist_ok=True)

    print("Creating AgriSense database...")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print("  → Creating tables...")
    create_tables(cur)

    print("  → Seeding 20 Nigerian crops...")
    seed_crops(cur)

    print("  → Seeding pests and diseases...")
    seed_pests(cur)

    print("  → Seeding treatments and costs...")
    seed_treatments(cur)

    print("  → Seeding fertilizer schedules...")
    seed_fertilizers(cur)

    print("  → Seeding market prices...")
    seed_market_prices(cur)

    conn.commit()
    conn.close()

    size = os.path.getsize(DB_PATH) / 1024
    print(f"\n✓ Database created: data/agrisense.db ({size:.1f} KB)")
    print("✓ Phase 2 complete. Run Phase 3 to build the RAG pipeline.")


if __name__ == "__main__":
    main()