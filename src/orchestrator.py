from src.llm import chat 
from src.rag import search as query_knowledge
from src.database import (
    get_crop_info,
    get_pest_treatments,
    get_market_price,
    search_pest_by_name,
)
from src.vision import classify_leaf_image


SYSTEM_PROMPT = """You are AgriSense, an offline agricultural assistant for Nigerian smallholder farmers.

Rules:
- Give practical, specific advice — not generic farming tips.
- Always mention cost in Naira when discussing treatments or inputs.
- If a treatment/product is mentioned in the provided context, use that exact info.
- Keep answers short and actionable — farmers want clear next steps, not essays.
- If you're not sure about something, say so rather than guessing.
- Respond in the same language style the farmer used (Pidgin, English, etc).
"""


def handle_query(user_text: str, image_path: str = None) -> dict:
    """
    Main orchestration entry point.
    Returns a dict with the answer and any supporting data for the UI.
    """
    context_blocks = []
    vision_result = None

    # Step 1: If there's an image, run vision classification first
    if image_path:
        vision_result = classify_leaf_image(image_path)
        if vision_result and vision_result.get("confidence", 0) > 0.3:
            disease_name = vision_result["label"]
            confidence = vision_result["confidence"]
            context_blocks.append(
                f"[Vision analysis] Detected: {disease_name} "
                f"(confidence: {confidence:.0%})"
            )

            # Pull matching treatment from SQLite if we recognize this pest/disease
            pest_match = search_pest_by_name(disease_name)
            if pest_match:
                treatments = get_pest_treatments(pest_match["id"])
                if treatments:
                    treatment_text = "; ".join(
                        f"{t['method']} using {t['product_name']} "
                        f"({t['dosage']}, ~₦{t['cost_naira']})"
                        for t in treatments
                    )
                    context_blocks.append(f"[Known treatments] {treatment_text}")

    # Step 2: RAG retrieval from ChromaDB for general agronomic knowledge
    rag_results = query_knowledge(user_text, n_results=3)
    if rag_results:
        context_blocks.append("[Reference knowledge] " + " | ".join(r["text"] for r in rag_results))

    # Step 3: Structured lookups — try to detect crop/price mentions
    # (simple keyword check; can be made smarter later)
    market_info = get_market_price(user_text)
    if market_info:
        context_blocks.append(
            f"[Market data] {market_info['crop']} in {market_info['region']}: "
            f"₦{market_info['price_per_kg_naira']}/kg, "
            f"trend: {market_info['trend']}"
        )

    # Step 4: Assemble the final prompt
    if context_blocks:
        context_str = "\n".join(context_blocks)
        full_prompt = (
            f"Context information:\n{context_str}\n\n"
            f"Farmer's question: {user_text}\n\n"
            f"Using the context above where relevant, answer the farmer's question."
        )
    else:
        full_prompt = user_text

    # Step 5: Call the LLM
    answer = chat(prompt=full_prompt, system=SYSTEM_PROMPT)

    return {
        "answer": answer,
        "vision_result": vision_result,
        "had_context": len(context_blocks) > 0,
    }