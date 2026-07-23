# 📚 NaziranGPT Documentation Hub

Welcome to the central documentation index for **NaziranGPT**. Below you will find comprehensive documentation covering architecture, database schemas, API specifications, RAG/AI implementation, deployment strategies, and developer onboarding.

---

## 🗂️ Documentation Directory Index

| Document | Description |
| :--- | :--- |
| 🚀 **[Getting Started & Setup](getting-started.md)** | Step-by-step developer onboarding, Docker environment setup, local execution, and testing. |
| 🏗️ **[Architecture Design](architecture.md)** | Clean layered architecture, security controls, token rotation, and system boundaries. |
| 📊 **[Database Schema](database-schema.md)** | Entity Relationship Diagram (ERD), table definitions, relational indexes, and `pgvector` schemas. |
| 🔌 **[REST API Specifications](api-documentation.md)** | Complete REST API endpoint reference, request/response JSON schemas, and authentication headers. |
| 🤖 **[RAG Engine & AI System](rag-and-ai-system.md)** | Technical breakdown of text parsing, vector embedding generation, cosine search, and multi-domain ATS scoring. |
| ☁️ **[Production Deployment Guide](deployment.md)** | Step-by-step production deployment instructions for Render, Vercel, Neon, and Supabase. |

---

## 🌟 Key Features Overview

- **Multi-Domain Resume Parser & ATS Engine**: Evaluates candidate resumes across software engineering, business analysis, HR, finance, marketing, product, and operations.
- **Interactive Match Re-Scoring**: Allows candidates to paste target job descriptions and instantly calculate keyword compatibility scores.
- **RAG AI Career Coach**: Natural conversation powered by vector similarity search (`pgvector`) + Google Gemini 1.5 Flash.
- **Enterprise Security**: JWT authentication with automatic token rotation, bcrypt password hashing, and role-based access control.
