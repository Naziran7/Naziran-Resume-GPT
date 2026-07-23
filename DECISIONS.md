# Architecture & Technical Decisions log

This document details the architectural decisions and technical trade-offs made during the development of NaziranGPT. Use this as a reference and for interview discussions.

---

## 1. Project Organization: Monorepo with Separated Backend and Frontend

*   **Decision**: Organize the project as a single repository containing distinct directories for the backend (`backend/`) and frontend (`frontend/`), orchestrated using `docker-compose`.
*   **Alternatives Considered**:
    *   *Multiple repositories*: Harder to manage and coordinate migrations, schema changes, and deployments in the initial phases.
    *   *Single mixed directory*: Creates dependency clutter and conflicts between Node.js and Python.
*   **Trade-off & Rationale**: A monorepo layout enables synchronized version control, easy development setup with a single `docker-compose.yml`, and clear separation of concerns. Deployment to Vercel (frontend) and Render (backend) remains simple since both support folder-specific builds.

---

## 2. Backend Design: Layered Architecture (Clean/Hexagonal Adaptation)

*   **Decision**: Adopt a layered architecture: `api` -> `services` -> `repositories` -> `models`.
*   **Alternatives Considered**:
    *   *MVC*: Standard Django-like layout. Harder to separate pure business logic from ORM models.
    *   *Microservices*: Overkill for the current scope and MVP timeline.
*   **Trade-off & Rationale**: Encapsulating data access logic inside `repositories` and business logic inside `services` ensures that if we change our ORM (SQLAlchemy) or database patterns, the endpoints/business logic remain unaffected. This is extremely valuable for testing and maintaining code as it grows.

---

## 3. Database Vector Extension: PostgreSQL + pgvector (Phase 2 Preview)

*   **Decision**: Use PostgreSQL with `pgvector` instead of a dedicated vector database (like Pinecone, Chroma, or FAISS).
*   **Alternatives Considered**:
    *   *FAISS*: Good for offline/in-memory, but has no persistent relational linking out-of-the-box and makes database sync complex.
    *   *Pinecone*: Fully managed and scalable, but introduces external API dependencies, costs, and data synchronization overhead.
*   **Trade-off & Rationale**: `pgvector` keeps all application data (users, resumes, embeddings) in one ACID-compliant database. This simplifies queries, reduces infrastructure costs, ensures transactional safety, and facilitates relational filtering during vector similarity searches.

---

## 4. Embedding Model: Sentence Transformers all-MiniLM-L6-v2 (384 dimensions)

*   **Decision**: Use `all-MiniLM-L6-v2` for generating embeddings instead of OpenAI's `text-embedding-3-small` or Gemini Embeddings.
*   **Alternatives Considered**:
    *   *OpenAI Text Embeddings*: OpenAI generates highly dense vectors (1536d) but introduces paid network API costs and API request latencies.
    *   *Gemini Embeddings*: Similar to OpenAI, requires internet connectivity and introduces per-call execution overhead.
*   **Trade-off & Rationale**: `all-MiniLM-L6-v2` runs locally and is extremely fast. Its 384-dimensional space is compact, lowering memory requirements on our PostgreSQL HNSW index. This speeds up vector distance calculations (`<=>`) while maintaining good semantic retrieval accuracy for standard document sizes.

---

## 5. Background Ingestion: FastAPI BackgroundTasks instead of Celery

*   **Decision**: Run embedding generation asynchronously using FastAPI's standard `BackgroundTasks` framework.
*   **Alternatives Considered**:
    *   *Celery*: Standard choice for heavy asynchronous task distribution. However, Celery introduces significant infrastructure overhead (requires a separate queue broker like RabbitMQ, worker runner processes, and extra deployment container services).
*   **Trade-off & Rationale**: In the MVP, document ingestion occurs sequentially. Embedding generation for a standard document takes less than 2 seconds with `all-MiniLM-L6-v2`. FastAPI's `BackgroundTasks` processes files asynchronously inside the existing backend event loop, avoiding architectural bloat. We will pivot to Celery in future phases only if retries or scheduled tasks are required.

---

## 6. Live Agent Response: Server-Sent Events (SSE) instead of WebSockets

*   **Decision**: Use SSE to stream LLM responses to the frontend.
*   **Alternatives Considered**:
    *   *WebSockets*: Standard choice for bi-directional live communication. However, it requires complex protocol handling, handshake states, and stateful socket preservation.
*   **Trade-off & Rationale**: AI Chatbot streaming is unidirectional: the user asks a question, and the server yields tokens sequentially. SSE runs over standard HTTP, respects proxy headers, automatically supports reconnections, and works natively with FastAPI generators, making it highly reliable and lightweight.

