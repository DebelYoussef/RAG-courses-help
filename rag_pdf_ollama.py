# rag_pdf_ollama.py — Version Ollama (sans clé API)
import os
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_ollama import ChatOllama          # ← Changé
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

DATA_DIR       = Path("data")
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
OLLAMA_MODEL   = "llama3"                         # ← Changé
CHUNK_SIZE     = 800
CHUNK_OVERLAP  = 150
TOP_K          = 3


def load_pdf_documents(data_dir):
    pdf_paths = sorted(data_dir.glob("*.pdf"))
    if not pdf_paths:
        raise FileNotFoundError("Aucun PDF dans data/")
    documents = []
    for pdf_path in pdf_paths:
        loader = PyPDFLoader(str(pdf_path))
        pages = loader.load()
        for page in pages:
            page.metadata["source"] = pdf_path.name
        documents.extend(pages)
    return documents


def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_documents(documents)
def create_vectorstore(chunks):
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    return FAISS.from_documents(chunks, embeddings)


def build_prompt():
    template = """
Tu es un assistant pédagogique spécialisé en IA générative.
Réponds uniquement à partir du contexte fourni.

Consignes :
- Réponds en français.
- Si l'info n'est pas dans le contexte, dis-le clairement.
- Donne une réponse claire, structurée et concise.
- Termine par "Sources :" avec les fichiers utilisés.

Contexte :
{context}

Question :
{question}
"""
    return PromptTemplate.from_template(template)
def format_context(docs):
    parts = []
    for i, doc in enumerate(docs, start=1):
        source = doc.metadata.get("source", "?")
        page = doc.metadata.get("page", "?")
        if isinstance(page, int):
            page += 1
        parts.append(
            f"[Extrait {i} | {source} | page {page}]\n{doc.page_content}"
        )
    return "\n\n".join(parts)


def format_sources(docs):
    seen = []
    for doc in docs:
        src = doc.metadata.get("source", "?")
        pg = doc.metadata.get("page", "?")
        if isinstance(pg, int):
            pg += 1
        item = f"{src} (page {pg})"
        if item not in seen:
            seen.append(item)
    return ", ".join(seen)

def answer_question(question, retriever, llm, prompt):
    docs = retriever.invoke(question)
    context = format_context(docs)
    sources = format_sources(docs)
    final_prompt = prompt.format(context=context, question=question)
    response = llm.invoke(final_prompt).content
    if "Sources :" not in response:
        response = response.strip() + f"\n\nSources : {sources}"
    return response, docs


def main():
    print("Chargement des PDF...")
    documents = load_pdf_documents(DATA_DIR)
    print(f"  {len(documents)} pages chargées")

    print("Découpage en chunks...")
    chunks = split_documents(documents)
    print(f"  {len(chunks)} chunks créés")

    print("Création des embeddings et index FAISS...")
    vectorstore = create_vectorstore(chunks)
    retriever = vectorstore.as_retriever(search_kwargs={"k": TOP_K})
    
    llm = ChatOllama(model=OLLAMA_MODEL, temperature=0)  # ← Changé
    prompt = build_prompt()

    print("\nAssistant RAG prêt. Tapez 'quit' pour quitter.\n")
    while True:
        question = input("Question > ").strip()
        if not question:
            continue
        if question.lower() in {"quit", "exit", "q"}:
            break
        answer, docs = answer_question(question, retriever, llm, prompt)
        print("\n--- Réponse ---")
        print(answer)
        print("\n--- Chunks récupérés ---")
        for i, doc in enumerate(docs, 1):
            src = doc.metadata.get("source", "?")
            pg = doc.metadata.get("page", "?")
            if isinstance(pg, int):
                pg += 1
            print(f"{i}. {src} | page {pg}")
            print(f"   {doc.page_content[:200].replace(chr(10),' ')}...")
        print()


if __name__ == "__main__":
    main()
