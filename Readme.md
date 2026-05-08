# 📄 RAG PDF Assistant

A fully local AI-powered assistant that lets you **chat with your PDF documents** — no API key required. Built with **LangChain**, **FAISS**, **Ollama (llama3)**, **FastAPI**, and **React**.

> Upload your PDFs, ask questions, get accurate answers with page-level citations — 100% offline.

---

## 🧠 Architecture

```
┌─────────────────┐        ┌──────────────────────────────────────┐
│   React UI      │───────▶│           FastAPI Backend             │
│  localhost:3000 │◀───────│  /upload  /chat  /update-chunking    │
└─────────────────┘        └─────────────────┬────────────────────┘
                                             │
                               ┌─────────────▼────────────┐
                               │       RAG Core            │
                               │  PyPDFLoader              │
                               │       ↓                   │
                               │  RecursiveTextSplitter    │
                               │       ↓                   │
                               │  HuggingFace Embeddings   │
                               │       ↓                   │
                               │  FAISS Vector Store       │
                               │       ↓                   │
                               │  Prompt Template          │
                               │       ↓                   │
                               │  ChatOllama (llama3)      │
                               └───────────────────────────┘
```

---

## ✨ Features

- 📂 Upload multiple PDFs via the web UI
- 🔍 Semantic search with FAISS + HuggingFace embeddings
- 🤖 Fully local LLM — runs offline with Ollama (llama3)
- 💬 Chat interface with source citations (filename + page number)
- 🔄 Dynamic re-indexing — add PDFs without restarting
- 📋 Swagger UI auto-generated at `http://127.0.0.1:8000/docs`

---

## 🗂️ Project Structure

```
project/
├── data/                    # Drop your PDF files here (git-ignored)
├── rag_pdf_ollama.py        # RAG core logic (chunking, FAISS, LLM)
├── main.py                  # FastAPI backend
├── requirements.txt         # Python dependencies
├── .gitignore
├── README.md
└── frontend/                # React app (create-react-app)
    ├── public/
    └── src/
        └── App.js           # Chat UI
```

---

## ⚙️ Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.10+ | [python.org](https://python.org) |
| Node.js | 16+ | [nodejs.org](https://nodejs.org) |
| Ollama | latest | [ollama.com](https://ollama.com) |

---

## 🚀 Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/your-username/rag-pdf-assistant.git
cd rag-pdf-assistant
```

### 2. Install Ollama and pull llama3

```bash
ollama pull llama3
ollama serve
```

### 3. Set up the Python backend

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
```

### 4. Start the FastAPI backend

```bash
uvicorn main:app --reload
```

→ Swagger UI at **http://127.0.0.1:8000/docs**

### 5. Start the React frontend

```bash
cd frontend
npm install
npm start
```

→ App at **http://localhost:3000**

---

## 📦 requirements.txt

```
fastapi
uvicorn[standard]
python-multipart
langchain
langchain-community
langchain-ollama
langchain-huggingface
langchain-text-splitters
langchain-core
faiss-cpu
pypdf
sentence-transformers
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/status` | Index status and loaded files |
| `POST` | `/upload` | Upload PDF(s) and rebuild index |
| `POST` | `/chat` | Ask a question, get answer + sources |
| `POST` | `/update-chunking` | Rebuild index from existing PDFs |
| `DELETE` | `/documents/{filename}` | Delete a PDF and rebuild |
| `GET` | `/docs` | Swagger UI |

---

## 🛠️ Configuration

Edit the top of `rag_pdf_ollama.py`:

```python
OLLAMA_MODEL  = "llama3"
CHUNK_SIZE    = 800
CHUNK_OVERLAP = 150
TOP_K         = 3
```

---

## 💡 How It Works

1. **Upload** — PDFs saved to `data/` and loaded page by page
2. **Chunk** — Text split into overlapping chunks
3. **Embed** — Each chunk converted to a vector via HuggingFace
4. **Index** — Vectors stored in FAISS
5. **Query** — Your question matched against the index
6. **Generate** — Top-K chunks sent to llama3 with a prompt template
7. **Answer** — Structured response with source citations

---

## 📜 License

[MIT](LICENSE)

---

## 👤 Author

Built with LangChain + Ollama + FastAPI + React