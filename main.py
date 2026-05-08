"""
main.py — FastAPI Backend for RAG PDF Assistant
Run: uvicorn main:app --reload
Swagger UI: http://127.0.0.1:8000/docs
"""

import shutil
from pathlib import Path
from typing import List

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Import your existing RAG logic ──────────────────────────────────────────
from rag_pdf_ollama import (
    load_pdf_documents,
    split_documents,
    create_vectorstore,
    build_prompt,
    answer_question,
)
from langchain_ollama import ChatOllama

# ── Config ───────────────────────────────────────────────────────────────────
DATA_DIR    = Path("data")
OLLAMA_MODEL = "llama3"
TOP_K       = 3
DATA_DIR.mkdir(exist_ok=True)

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="RAG PDF Assistant",
    description="Ask questions about your PDFs using llama3 + FAISS + LangChain",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # React frontend
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global RAG state ──────────────────────────────────────────────────────────
rag_state: dict = {
    "retriever": None,
    "llm": None,
    "prompt": None,
    "loaded_files": [],
}

def rebuild_index():
    """Reload all PDFs and rebuild the FAISS index."""
    documents = load_pdf_documents(DATA_DIR)
    chunks    = split_documents(documents)
    vectorstore = create_vectorstore(chunks)
    rag_state["retriever"]    = vectorstore.as_retriever(search_kwargs={"k": TOP_K})
    rag_state["llm"]          = ChatOllama(model=OLLAMA_MODEL, temperature=0)
    rag_state["prompt"]       = build_prompt()
    rag_state["loaded_files"] = [p.name for p in sorted(DATA_DIR.glob("*.pdf"))]
    return len(chunks)


# ── Pydantic Schemas ──────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[str]

class UploadResponse(BaseModel):
    message: str
    files: List[str]
    chunks: int

class StatusResponse(BaseModel):
    ready: bool
    loaded_files: List[str]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/", tags=["General"])
def root():
    return {"message": "RAG API is running. Visit /docs for Swagger UI."}


@app.get("/status", response_model=StatusResponse, tags=["General"])
def status():
    """Check if the RAG index is loaded and which files are indexed."""
    return {
        "ready": rag_state["retriever"] is not None,
        "loaded_files": rag_state["loaded_files"],
    }


@app.post("/upload", response_model=UploadResponse, tags=["Documents"])
async def upload_pdfs(files: List[UploadFile] = File(...)):
    """
    Upload one or more PDF files and rebuild the FAISS index automatically.
    """
    saved = []
    for file in files:
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail=f"{file.filename} is not a PDF.")
        dest = DATA_DIR / file.filename
        with dest.open("wb") as f:
            shutil.copyfileobj(file.file, f)
        saved.append(file.filename)

    try:
        chunks = rebuild_index()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Index build failed: {e}")

    return {
        "message": f"{len(saved)} file(s) uploaded and indexed.",
        "files": saved,
        "chunks": chunks,
    }


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
def chat(request: ChatRequest):
    """
    Ask a question. The RAG system retrieves relevant chunks from PDFs
    and generates an answer using llama3.
    """
    if rag_state["retriever"] is None:
        raise HTTPException(
            status_code=400,
            detail="No PDFs indexed yet. Upload PDFs first via /upload."
        )

    try:
        answer, docs = answer_question(
            request.question,
            rag_state["retriever"],
            rag_state["llm"],
            rag_state["prompt"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    sources = []
    seen = set()
    for doc in docs:
        src = doc.metadata.get("source", "?")
        pg  = doc.metadata.get("page", "?")
        if isinstance(pg, int):
            pg += 1
        label = f"{src} (page {pg})"
        if label not in seen:
            sources.append(label)
            seen.add(label)

    return {"answer": answer, "sources": sources}


@app.post("/update-chunking", tags=["Documents"])
def update_chunking():
    """
    Rebuild the FAISS index from all PDFs already in the data/ folder.
    Useful after manually adding/removing files.
    """
    try:
        chunks = rebuild_index()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="No PDFs found in data/ folder.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "message": "Index rebuilt successfully.",
        "chunks": chunks,
        "files": rag_state["loaded_files"],
    }


@app.delete("/documents/{filename}", tags=["Documents"])
def delete_document(filename: str):
    """Delete a PDF and rebuild the index."""
    target = DATA_DIR / filename
    if not target.exists():
        raise HTTPException(status_code=404, detail=f"{filename} not found.")
    target.unlink()
    try:
        rebuild_index()
    except FileNotFoundError:
        rag_state["retriever"] = None
        rag_state["loaded_files"] = []
    return {"message": f"{filename} deleted."}