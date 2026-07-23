# NaziranGPT — AI-Powered Career Intelligence Platform

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React_19-61DAFB?style=flat-square&logo=react)](https://react.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind_v4-06B6D4?style=flat-square&logo=tailwindcss)](https://tailwindcss.com/)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL_%2B_pgvector-4169E1?style=flat-square&logo=postgresql)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Infrastructure-Docker_Compose-2496ED?style=flat-square&logo=docker)](https://www.docker.com/)

**NaziranGPT** is a production-ready SaaS platform built to empower students and professionals in their career journeys. It leverages artificial intelligence and natural language processing to deliver automated resume parsing, ATS compatibility scoring, actionable feedback, interactive AI career coaching (RAG chatbot), and downloadable PDF analytical reports.

---

## 📋 Table of Contents

- [NaziranGPT — AI-Powered Career Intelligence Platform](#nazirangpt--ai-powered-career-intelligence-platform)
  - [📋 Table of Contents](#-table-of-contents)
  - [✨ Features](#-features)
  - [🛠️ Tech Stack](#️-tech-stack)
    - [Frontend](#frontend)
    - [Backend](#backend)
    - [Infrastructure \& Database](#infrastructure--database)
  - [📂 Project Directory Structure](#-project-directory-structure)
  - [⚙️ Environment Configuration](#️-environment-configuration)
    - [Key Environment Variables](#key-environment-variables)
  - [🚀 How to Run the Project](#-how-to-run-the-project)
    - [Prerequisites](#prerequisites)
    - [Method A: Run via Docker Compose (Recommended)](#method-a-run-via-docker-compose-recommended)
    - [Method B: Manual Local Setup (Native Development)](#method-b-manual-local-setup-native-development)
      - [Step 1: Start PostgreSQL and Redis](#step-1-start-postgresql-and-redis)
      - [Step 2: Setup and Start Backend](#step-2-setup-and-start-backend)
      - [Step 3: Setup and Start Frontend](#step-3-setup-and-start-frontend)
  - [🔑 API Documentation \& Endpoints](#-api-documentation--endpoints)
    - [Key Endpoint Routes (`/api/v1`)](#key-endpoint-routes-apiv1)
  - [🗄️ Database Management \& Migrations](#️-database-management--migrations)
  - [🧪 Testing \& Verification](#-testing--verification)
    - [Backend Automated Unit \& Integration Tests](#backend-automated-unit--integration-tests)
    - [Frontend Quality \& End-to-End Tests](#frontend-quality--end-to-end-tests)
  - [🚢 Production Deployment](#-production-deployment)
    - [Render Deployment (Backend \& Database)](#render-deployment-backend--database)
    - [Vercel / Netlify Deployment (Frontend)](#vercel--netlify-deployment-frontend)
  - [📄 Documentation Links](#-documentation-links)
  - [👨‍💻 Author \& License](#-author--license)

---

## ✨ Features

- **🔒 Secure Authentication & Token Rotation**: JWT-based authentication featuring short-lived access tokens, long-lived refresh tokens with automatic single-use token rotation, and BCrypt password hashing.
- **📄 Multi-Engine Resume Parsing**: Dynamic extraction from `.pdf` and `.docx` files using `pdfplumber`, `python-docx`, `spaCy` NLP, with automatic fallback to Google Gemini AI LLM.
- **🎯 ATS Compatibility Scoring Engine**: Detailed algorithmic evaluation of candidate resumes against ATS (Applicant Tracking System) criteria, yielding scores for keywords, experience, formatting, and skills.
- **💬 AI Career Coach Chatbot (RAG)**: Interactive vector-search-assisted chatbot (pgvector + Google Gemini / Sentence Transformers) allowing users to ask questions directly about their uploaded resumes and targeted job roles.
- **📊 Downloadable PDF Reports**: Automated generation of styled, comprehensive PDF career audit reports powered by `ReportLab`.
- **📧 Automated Email Notifications**: Integrated password reset and transactional emails via `Resend`.
- **⚡ Rate Limiting & Protection**: Endpoint abuse protection powered by `slowapi`.

---

## 🛠️ Tech Stack

### Frontend
- **Framework**: React 19 (TypeScript, Vite)
- **Styling**: Tailwind CSS v4, Lucide React icons, Glassmorphism UI tokens
- **Routing & State**: React Router v7, React Query, custom AuthContext
- **HTTP Client**: Axios with automated 401 JWT refresh token interceptors
- **Linting & Code Quality**: Oxlint

### Backend
- **Framework**: Python 3.11+, FastAPI
- **Database ORM**: SQLAlchemy 2.0 (Async Engine via `asyncpg` & sync fallback via `psycopg2`)
- **Database Migrations**: Alembic
- **Validation**: Pydantic v2 & Pydantic-Settings
- **Security & Hashing**: Passlib with BCrypt, Python-Jose (JWT)
- **NLP & AI Engine**: Google Gemini API (`google-generativeai`), spaCy (`en_core_web_sm`), `pdfplumber`, `python-docx`
- **PDF Generation**: ReportLab
- **Rate Limiting**: Slowapi (IP-based throttling)

### Infrastructure & Database
- **Primary Database**: PostgreSQL 15/16 with `pgvector` extension for vector embeddings
- **Caching & Session Broker**: Redis 7
- **Containerization**: Docker & Docker Compose
- **Cloud Deployment**: Render (`render.yaml`), Vercel / Nginx

---

## 📂 Project Directory Structure

```text
Naziran-GPT/
├── backend/
│   ├── alembic/              # Database migration scripts
│   ├── app/
│   │   ├── api/              # Versioned API endpoints (v1: auth, resumes, chatbot)
│   │   ├── core/             # App configs, security utilities, CORS, rate limiter
│   │   ├── models/           # SQLAlchemy database tables (User, Resume, Session)
│   │   ├── repositories/     # Data access abstraction layer (CRUD logic)
│   │   ├── schemas/          # Pydantic schemas for request validation & response serialization
│   │   ├── services/         # Core business logic (Parser, Scoring, AI Chatbot, Storage, Email)
│   │   └── main.py           # FastAPI application entrypoint & middleware configuration
│   ├── uploads/              # Storage directory for uploaded user documents
│   ├── Dockerfile            # Container definition for Python FastAPI backend
│   └── requirements.txt      # Python dependencies
├── frontend/
│   ├── e2e/                  # Playwright end-to-end automated tests
│   ├── src/
│   │   ├── components/       # Shared UI components & protected route wrappers
│   │   ├── context/          # Authentication state management
│   │   ├── lib/              # Axios HTTP client configuration & interceptors
│   │   └── pages/            # View pages (Login, Register, Dashboard, Profile)
│   ├── Dockerfile            # Container definition (Multi-stage build with Nginx)
│   ├── nginx.conf            # Production Nginx reverse proxy configuration
│   └── package.json          # Node.js dependencies & scripts
├── docs/                     # Architecture, database schema, & deployment documentation
├── .env                      # Local environment configuration file (ignored by Git)
├── .env.example              # Template environment variables
├── DECISIONS.md              # Architectural decisions & technical trade-offs log
├── docker-compose.yml        # Multi-container orchestration (DB, Redis, Backend, Frontend)
├── render.yaml               # Infrastructure-as-code specification for Render cloud
└── README.md                 # Project documentation
```

---

## ⚙️ Environment Configuration

Copy `.env.example` to `.env` in the root directory before launching the application:

```bash
cp .env.example .env
```

### Key Environment Variables

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `ENVIRONMENT` | Runtime environment (`development`, `production`, `test`) | `development` |
| `POSTGRES_USER` | PostgreSQL username | `postgres` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `Nazi` |
| `POSTGRES_DB` | PostgreSQL database name | `nazirangpt` |
| `POSTGRES_SERVER` | PostgreSQL server hostname | `localhost` (or `db` for Docker) |
| `POSTGRES_PORT` | PostgreSQL port | `5432` |
| `SECRET_KEY` | Secret key used for signing JWT tokens | Generate via `openssl rand -hex 32` |
| `GEMINI_API_KEY` | Google Gemini API Key for AI features & LLM parsing | `your_gemini_api_key_here` |
| `RESEND_API_KEY` | Resend API Key for transactional email delivery | `your_resend_api_key` |
| `BACKEND_CORS_ORIGINS` | Allowed CORS origins (comma-separated or `*`) | `http://localhost:3000,http://localhost:5173` |

> 💡 **Note on AI Features**: If `GEMINI_API_KEY` is omitted or left empty, the application gracefully falls back to local regex and spaCy parsing rules.

---

## 🚀 How to Run the Project

### Prerequisites

Ensure you have the following installed on your machine:
- [Git](https://git-scm.com/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Required for Method A)
- [Python 3.11+](https://www.python.org/downloads/) (Required for manual Backend execution)
- [Node.js 18+](https://nodejs.org/) & `npm` (Required for manual Frontend execution)

---

### Method A: Run via Docker Compose (Recommended)

This method spins up all 4 required services simultaneously: PostgreSQL with `pgvector`, Redis 7, FastAPI Backend, and Nginx React Frontend.

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-repo/Naziran-GPT.git
   cd Naziran-GPT
   ```

   *(Update `GEMINI_API_KEY` in `.env` if you want AI chatbot & Gemini features enabled)*

2. **Build and Launch Containers**:
   ```bash
   docker-compose up --build
   ```

3. **Access the Running Services**:
   - **Frontend Application**: [http://localhost:3000](http://localhost:3000)
   - **FastAPI Backend API**: [http://localhost:8000](http://localhost:8000)
   - **Interactive API Documentation (Swagger)**: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
   - **ReDoc API Documentation**: [http://localhost:8000/api/v1/redoc](http://localhost:8000/api/v1/redoc)

4. **Stop Containers**:
   ```bash
   docker compose down
   ```

---

### Method B: Manual Local Setup (Native Development)

If you wish to run the backend and frontend natively without containers:

#### Step 1: Start PostgreSQL and Redis
Ensure a PostgreSQL database (port `5432`) and Redis server (port `6379`) are running locally, matching your `.env` configuration.

#### Step 2: Setup and Start Backend

1. Navigate to the `backend/` directory:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   ```bash
   # On Windows (PowerShell)
   python -m venv .venv
   .venv\Scripts\activate

   # On macOS / Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Download the spaCy NLP language model:
   ```bash
   python -m spacy download en_core_web_sm
   ```

5. Run database migrations with Alembic:
   ```bash
   alembic upgrade head
   ```

6. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

   The backend will be live at `http://localhost:8000`.

#### Step 3: Setup and Start Frontend

1. Open a new terminal and navigate to `frontend/`:
   ```bash
   cd frontend
   ```

2. Install Node.js dependencies:
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```

   The frontend will be live at `http://localhost:5173` (or `http://localhost:3000`).

---

## 🔑 API Documentation & Endpoints

FastAPI automatically generates interactive Swagger documentation. When the backend is running, open:
👉 **[http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)**

### Key Endpoint Routes (`/api/v1`)

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/api/v1/auth/register` | Register a new user account | ❌ |
| `POST` | `/api/v1/auth/login` | Authenticate user & receive access/refresh JWT tokens | ❌ |
| `POST` | `/api/v1/auth/refresh` | Obtain new access token using valid refresh token | ❌ |
| `POST` | `/api/v1/auth/logout` | Revoke current user session |  |
| `GET` | `/api/v1/auth/me` | Fetch authenticated user profile |  |
| `POST` | `/api/v1/resumes/upload` | Upload resume file (`.pdf`, `.docx`) for processing |  |
| `GET` | `/api/v1/resumes/` | List all uploaded resumes for the current user |  |
| `GET` | `/api/v1/resumes/{id}` | Get detailed ATS score breakdown & parsed data |  |
| `GET` | `/api/v1/resumes/{id}/pdf` | Download formatted ATS feedback report (PDF) |  |
| `POST` | `/api/v1/chatbot/query` | Send query to AI Career Coach (RAG streaming response) |  |

---

## 🗄️ Database Management & Migrations

NaziranGPT uses **Alembic** for schema migration tracking.

- **Apply all pending migrations**:
  ```bash
  cd backend
  alembic upgrade head
  ```

- **Generate a new migration after modifying models**:
  ```bash
  cd backend
  alembic revision --autogenerate -m "Add custom field to resumes"
  ```

- **Roll back the last applied migration**:
  ```bash
  cd backend
  alembic downgrade -1
  ```

---

## 🧪 Testing & Verification

### Backend Automated Unit & Integration Tests

Backend tests use `pytest` and `pytest-asyncio`. Run them inside the `backend/` directory:

```bash
cd backend
pytest -v
```

### Frontend Quality & End-to-End Tests

1. **Linting (Oxlint)**:
   ```bash
   cd frontend
   npm run lint
   ```

2. **E2E Playwright Automation**:
   ```bash
   cd frontend
   npx playwright install
   npx playwright test
   ```

---

## 🚢 Production Deployment

### Render Deployment (Backend & Database)

The project includes a ready-to-use Blueprint configuration in [`render.yaml`](file:///c:/Users/ANISH%20NAZIRAN/OneDrive/Documents/Naziran%20Matrix%20&%20GPT%20Projects/Naziran-GPT/render.yaml):

1. Connect your GitHub repository to [Render](https://render.com/).
2. Select **Blueprints** and point Render to `render.yaml`.
3. Render will automatically provision:
   - PostgreSQL database with `pgvector` enabled
   - Redis cache instance
   - FastAPI web service with Docker runtime
4. Configure required secrets (`GEMINI_API_KEY`, `RESEND_API_KEY`) in the Render Dashboard.

### Vercel / Netlify Deployment (Frontend)

1. Connect the `frontend/` subdirectory to [Vercel](https://vercel.com/).
2. Set Build Command: `npm run build`
3. Set Output Directory: `dist`
4. Configure Environment Variable: `VITE_API_BASE_URL=https://your-backend-render-url.onrender.com/api/v1`

---

## 📄 Documentation Links

- [Architecture Design Document](file:///c:/Users/ANISH%20NAZIRAN/OneDrive/Documents/Naziran%20Matrix%20&%20GPT%20Projects/Naziran-GPT/docs/architecture.md)
- [Database Schema Document](file:///c:/Users/ANISH%20NAZIRAN/OneDrive/Documents/Naziran%20Matrix%20&%20GPT%20Projects/Naziran-GPT/docs/database-schema.md)
- [Deployment Guide](file:///c:/Users/ANISH%20NAZIRAN/OneDrive/Documents/Naziran%20Matrix%20&%20GPT%20Projects/Naziran-GPT/docs/deployment.md)
- [Architectural Decisions Log](file:///c:/Users/ANISH%20NAZIRAN/OneDrive/Documents/Naziran%20Matrix%20&%20GPT%20Projects/Naziran-GPT/DECISIONS.md)

---

## 👨‍💻 Author & License

Developed with ❤️ as part of the **NaziranGPT** career intelligence platform. Distributed under the MIT License.
