import logging
from app.adapters.fallback import fallback_orchestrator

logger = logging.getLogger("agrigo.seed")

INITIAL_AGRICULTURAL_FACTS = [
    {
        "id": "kb-1",
        "title": "Tomato Leaf Curling Disease (ToLCD)",
        "category": "diseases",
        "crop": "Tomato",
        "content": "Leaf curl in tomato is transmitted by the whitefly Bemisia tabaci. Symptoms include upward curling of leaves, leaf thickening, and stunted plant growth. Organic management involves spraying 5ml neem oil/liter and installing yellow sticky traps (15 traps per acre) to control whiteflies."
    },
    {
        "id": "kb-2",
        "title": "Wheat Nitrogen Management & Crown Root Irrigation",
        "category": "irrigation",
        "crop": "Wheat",
        "content": "The Crown Root Initiation (CRI) stage occurs 20-25 days after sowing and is the most critical irrigation stage for wheat. Delaying CRI irrigation reduces tillering and overall yield significantly. Apply top-dress urea right after this irrigation."
    },
    {
        "id": "kb-3",
        "title": "Drip Irrigation Best Practices for Vegetables",
        "category": "irrigation",
        "crop": "Vegetables",
        "content": "Drip irrigation saves 40-60% water compared to furrow irrigation. Operate drip systems during early mornings or late afternoons. Clean disc/screen filters weekly to prevent emitter clogging."
    },
    {
        "id": "kb-4",
        "title": "Biological Pest Control with Trichoderma & Pseudomonas",
        "category": "pesticides",
        "crop": "General",
        "content": "Trichoderma viride is an effective bio-fungicide against soil-borne root rot and damping off. Treat seeds with 10g Trichoderma per kg seed before sowing. Combine with well-rotted Farm Yard Manure (FYM) for soil application."
    }
]

async def seed_initial_knowledge():
    for fact in INITIAL_AGRICULTURAL_FACTS:
        await fallback_orchestrator.vector_store.add_document(
            doc_id=fact["id"],
            text=f"{fact['title']}. {fact['content']}",
            metadata={"title": fact["title"], "category": fact["category"], "crop": fact["crop"]}
        )
    logger.info("Initial agricultural knowledge base successfully seeded into Vector Store.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(seed_initial_knowledge())
