from fastapi import APIRouter, HTTPException
from app.models.knowledge import KnowledgeDocCreate, KnowledgeSearchRequest
from app.adapters.fallback import fallback_orchestrator
import uuid

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base & RAG"])

IN_MEMORY_KNOWLEDGE = []

@router.post("/")
async def create_knowledge_doc(doc: KnowledgeDocCreate):
    doc_id = str(uuid.uuid4())
    record = doc.dict()
    record["id"] = doc_id
    IN_MEMORY_KNOWLEDGE.append(record)
    
    # Add to Vector Store
    await fallback_orchestrator.vector_store.add_document(
        doc_id=doc_id,
        text=f"{doc.title}. {doc.content}",
        metadata={"title": doc.title, "category": doc.category, "crop": doc.crop}
    )
    return record

@router.get("/")
async def list_knowledge_docs():
    return IN_MEMORY_KNOWLEDGE

@router.post("/search")
async def search_knowledge(req: KnowledgeSearchRequest):
    return await fallback_orchestrator.vector_store.search(req.query, limit=req.limit)
