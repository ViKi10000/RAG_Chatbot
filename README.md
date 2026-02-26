# RAG-Chatbot — Domain-Specific QA over Documents

This project is a simple Retrieval-Augmented Generation (RAG) chatbot. It answers questions **only** from a set of local documents (PDF/TXT) and avoids hallucinating answers beyond those documents.

---



## How it works (architecture)

**Backend (FastAPI, Python)**

- `DataLoader` (`backend/src/data_loader.py`)
  - Loads PDFs and text files from `./data`.
  - Splits them into smaller text chunks with metadata (source file, page, etc.).

- `EmbeddingManager` and `VectorStore` (`backend/src/embedding.py`, `backend/src/vectorstore.py`)
  - Converts chunks into embeddings using a sentence-transformer model.
  - Stores embeddings and metadata in a ChromaDB collection.

- `RAGRetriever` (`backend/src/search.py`)
  - Given a question, creates a query embedding.
  - Retrieves the most similar chunks from the vector store.

- `GroqLLM` and `RAGPipeline` (`backend/src/llm.py`)
  - Builds a short prompt with the retrieved chunks as **Context**.
  - Uses a Groq chat model to generate an answer.
  - If there are **no retrieved chunks**, it does **not** call the model and simply returns:
    > `No context about this question.`

- `main.py` (FastAPI app)
  - Endpoints:
    - `GET /health` – basic health check.
    - `POST /init` – (re)initialize pipeline if needed.
    - `POST /query` – run the full RAG flow for a question.
    - `GET /status` – show whether the pipeline is ready and how many chunks are indexed.

**Frontend (React + Vite + Tailwind)**

- Very small, single-page UI:
  - Dark header with title, `Initialize` button, `Clear chat` button, and simple “Ready (N chunks)” text.
  - One chat panel with:
    - Message list (user/bot/system/error).
    - Textarea + Send button.
  - Error or “no context” responses are shown directly as bot messages.

---

## Design decisions

- **RAG over fine-tuning:** We use retrieval-augmented generation so the chatbot can be updated by changing documents in `./data` without retraining. Any LLM can be swapped (e.g. via `GROQ_LLM_MODEL`).
- **Embeddings and vector store:** Sentence-transformers (`all-MiniLM-L6-v2`) produce embeddings; ChromaDB stores them so we can do fast similarity search. The store is persisted under `./data/vector_store`.
- **Strict grounding and hallucination prevention:**
  - The retriever returns the most relevant document chunks for each question.
  - If **no chunks** are found, the backend skips the LLM and returns: `No context about this question.`
  - The LLM prompt instructs the model to answer **only** from the provided context and to reply `No context about this question.` when the context does not contain the answer.
  - Answers are kept short (1–3 sentences) via prompt and a lower `max_tokens` limit.
- **Simple UI:** Single-page chat (no sidebar or modals) so the app stays minimal and easy to run.

---

## Running the project locally

Clone this repository (or use your local copy), then run the following from the **project root**. Use a new terminal for the frontend.

### 1. Backend — prepare environment

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Backend — set API key

```powershell
$env:GROQ_API_KEY = "YOUR_GROQ_API_KEY"
```

Optional: override the default Groq model:

```powershell
$env:GROQ_LLM_MODEL = "llama-3.1-8b-instant"
```

### 3. Backend — start API

```powershell
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open API docs: `http://localhost:8000/docs`

### 4. Frontend — in a new terminal

```powershell
cd frontend
npm install
npm run dev
```

Open the application: `http://localhost:3000`

**Documents:** Place your PDFs in `backend/data/pdf` and your `.txt` files in `backend/data/text_files`. On startup, the backend loads and indexes everything in those folders. Create the folders if they do not exist.

---

## Potential improvements (if given more time)

- Better document admin:
  - Simple interface to upload/remove documents instead of using the `./data` folder directly.
- More robust search:
  - Add keyword filters or metadata filters (e.g. by document type).
- Better evaluation:
  - Add simple tests or scripts to compare retrieved chunks against expected answers.
- Observability:
  - Log retrieval scores and which documents were used for each answer to help debugging.
