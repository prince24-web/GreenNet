import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'agrisense.db')


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets you access columns by name
    return conn


def get_crop_by_name(name: str) -> dict:
    """Look up a crop by English or local name."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM crops 
        WHERE LOWER(name) LIKE LOWER(?) 
           OR LOWER(local_names) LIKE LOWER(?)
    """, (f"%{name}%", f"%{name}%"))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else {}


def get_pests_for_crop(crop_name: str) -> list[dict]:
    """Get all pests that affect a given crop."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM pests
        WHERE LOWER(affected_crops) LIKE LOWER(?)
    """, (f"%{crop_name}%",))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_treatments_for_pest(pest_id: int) -> list[dict]:
    """Get all treatments for a pest by pest ID."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM treatments WHERE pest_id = ?", (pest_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_fertilizers_for_crop(crop_id: int) -> list[dict]:
    """Get fertilizer schedule for a crop."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM fertilizers WHERE crop_id = ?", (crop_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_market_prices(crop_name: str, region: str = None) -> list[dict]:
    """Get current market prices, optionally filtered by region."""
    conn = get_connection()
    cur = conn.cursor()
    if region:
        cur.execute("""
            SELECT mp.*, c.name as crop_name FROM market_prices mp
            JOIN crops c ON mp.crop_id = c.id
            WHERE LOWER(c.name) LIKE LOWER(?)
              AND LOWER(mp.region) LIKE LOWER(?)
        """, (f"%{crop_name}%", f"%{region}%"))
    else:
        cur.execute("""
            SELECT mp.*, c.name as crop_name FROM market_prices mp
            JOIN crops c ON mp.crop_id = c.id
            WHERE LOWER(c.name) LIKE LOWER(?)
        """, (f"%{crop_name}%",))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_crops() -> list[dict]:
    """Return all crops — used for autocomplete and listing."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, local_names, growing_zones FROM crops")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def search_pests_by_symptom(symptom_keyword: str) -> list[dict]:
    """Find pests matching a symptom description — e.g. 'yellow leaves'."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM pests
        WHERE LOWER(symptoms) LIKE LOWER(?)
    """, (f"%{symptom_keyword}%",))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_full_crop_context(crop_name: str) -> str:
    """
    Master function — called by the orchestrator.
    Returns a single formatted text block with everything
    known about a crop, ready to inject into an LLM prompt.
    """
    crop = get_crop_by_name(crop_name)
    if not crop:
        return ""

    lines = [
        f"CROP: {crop['name']} (also called: {crop['local_names']})",
        f"Growing zones: {crop['growing_zones']}",
        f"Plant: {crop['planting_months']} | Harvest: {crop['harvest_months']}",
        f"Soil: {crop['soil_type']} | Water: {crop['water_needs']}",
        f"Expected yield: {crop['yield_per_hectare']}",
        f"Notes: {crop['notes']}",
        ""
    ]

    # Pests
    pests = get_pests_for_crop(crop['name'])
    if pests:
        lines.append("KNOWN PESTS & DISEASES:")
        for pest in pests:
            lines.append(f"  - {pest['name']} ({pest['type']}): {pest['symptoms']}")
            treatments = get_treatments_for_pest(pest['id'])
            for t in treatments:
                lines.append(f"    Treatment: {t['product_name']} — {t['dosage']} — ₦{t['cost_naira']} — {t['availability']}")
        lines.append("")

    # Fertilizers
    fertilizers = get_fertilizers_for_crop(crop['id'])
    if fertilizers:
        lines.append("FERTILIZER SCHEDULE:")
        for f in fertilizers:
            lines.append(f"  - {f['fertilizer_name']} ({f['npk_ratio']}) at {f['application_stage']}: {f['kg_per_hectare']} kg/ha, Week {f['timing_weeks']}, ₦{f['cost_naira_per_bag']}/bag")
        lines.append("")

    # Market prices
    prices = get_market_prices(crop['name'])
    if prices:
        lines.append("MARKET PRICES:")
        for p in prices:
            lines.append(f"  - {p['region']}: ₦{p['price_per_kg_naira']}/kg | ₦{p['price_per_bag_naira']}/bag ({p['trend']}) — {p['market_name']}")

    return "\n".join(lines)


def get_crop_info(crop_id_or_name) -> dict:
    """Get general details for a crop by ID or name."""
    if isinstance(crop_id_or_name, int):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM crops WHERE id = ?", (crop_id_or_name,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else {}
    else:
        return get_crop_by_name(crop_id_or_name)


def search_pest_by_name(name: str) -> dict:
    """Look up a pest by name or local name."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM pests 
        WHERE LOWER(name) LIKE LOWER(?) 
           OR LOWER(local_name) LIKE LOWER(?)
    """, (f"%{name}%", f"%{name}%"))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else {}


def get_pest_treatments(pest_id: int) -> list[dict]:
    """Get all treatments for a pest by pest ID (alias for get_treatments_for_pest)."""
    return get_treatments_for_pest(pest_id)


def get_market_price(query: str) -> dict:
    """
    Search the query for crop and region mentions.
    Returns the first matching market price as a dict, or {} if none.
    """
    # 1. Get all crops to search for their names in the query
    crops = get_all_crops()
    matched_crop = None
    for crop in crops:
        # Check if crop name or any of the local names are in the query
        if crop['name'].lower() in query.lower():
            matched_crop = crop
            break
        local_names = [n.strip() for n in crop.get('local_names', '').split(',') if n.strip()]
        for ln in local_names:
            if ln.lower() in query.lower():
                matched_crop = crop
                break
                
    if not matched_crop:
        return {}
        
    # 2. Check if a region is mentioned
    regions = ["Lagos", "Onitsha", "Ibadan", "Kano", "Abuja", "Kebbi", "Sokoto", "Kaduna"]
    matched_region = None
    for r in regions:
        if r.lower() in query.lower():
            matched_region = r
            break
            
    # 3. Query market prices
    conn = get_connection()
    cur = conn.cursor()
    if matched_region:
        cur.execute("""
            SELECT mp.*, c.name as crop_name FROM market_prices mp
            JOIN crops c ON mp.crop_id = c.id
            WHERE mp.crop_id = ? AND LOWER(mp.region) = LOWER(?)
        """, (matched_crop['id'], matched_region))
    else:
        # Default to the first region available for that crop
        cur.execute("""
            SELECT mp.*, c.name as crop_name FROM market_prices mp
            JOIN crops c ON mp.crop_id = c.id
            WHERE mp.crop_id = ?
            LIMIT 1
        """, (matched_crop['id'],))
        
    row = cur.fetchone()
    conn.close()
    
    if row:
        r = dict(row)
        return {
            "crop": r["crop_name"],
            "region": r["region"],
            "price_per_kg_naira": r["price_per_kg_naira"],
            "trend": r["trend"]
        }
    return {}