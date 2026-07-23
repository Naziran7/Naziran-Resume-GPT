# Getting Started & Local Development Guide

Welcome to the developer setup and local environment guide for **NaziranGPT**.

---

## 📋 Prerequisites

Ensure you have the following installed on your machine:
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Recommended)
- [Node.js v18+](https://nodejs.org/) & `npm`
- [Python 3.11+](https://www.python.org/)
- [Git](https://git-scm.com/)

---

## 🚀 Quickstart with Docker Compose (Recommended)

The simplest way to run the full application stack (Frontend + FastAPI Backend + PostgreSQL Vector Database + Redis) is via Docker Compose:

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/Naziran-GPT.git
   cd Naziran-GPT
   ```

2. **Configure Environment Variables**:
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   *(Optionally update `GEMINI_API_KEY` with your key from [Google AI Studio](https://aistudio.google.com/app/apikey))*

3. **Launch Docker Services**:
   ```bash
   docker-compose up --build
   ```

4. **Access the Applications**:
   - **Frontend App**: [http://localhost:3000](http://localhost:3000)
   - **FastAPI OpenAPI Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - **PostgreSQL Database**: Port `5433`

---

## 💻 Manual Local Setup (Without Docker)

### 1. Database Setup (PostgreSQL with pgvector)
Ensure PostgreSQL is running locally with the `vector` extension enabled:
```sql
CREATE DATABASE nazirangpt;
\c nazirangpt
CREATE EXTENSION IF NOT EXISTS vector;
```

---

### 2. Backend Setup (FastAPI)

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run database migrations:
   ```bash
   alembic upgrade head
   ```
5. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

---

### 3. Frontend Setup (React + Vite)

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install node dependencies:
   ```bash
   npm install
   ```
3. Start Vite dev server:
   ```bash
   npm run dev
   ```
4. Access the web interface at `http://localhost:5173` or `http://localhost:3000`.

---

## 🧪 Running Verification & Tests

### Frontend Build Test
```bash
cd frontend
npm run build
```

### Backend Test Suite
```bash
cd backend
pytest
```
