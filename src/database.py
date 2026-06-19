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