# REST API Specifications & Endpoint Reference

This document provides a detailed specification for all REST API endpoints exposed by the **NaziranGPT Backend API** (`/api/v1`).

---

## 🔐 Authentication & Headers

All protected endpoints require an HTTP `Authorization` header containing a valid Bearer JSON Web Token (JWT):

```http
Authorization: Bearer <access_token>
```

---

## 1. Authentication Endpoints (`/api/v1/auth`)

### `POST /auth/register`
Creates a new user account.

* **Request Body** (`application/json`):
  ```json
  {
    "email": "user@example.com",
    "password": "SecurePassword123!",
    "full_name": "Anish Naziran"
  }
  ```
* **Response** (`201 Created`):
  ```json
  {
    "id": "c1f7b80a-9d7a-4286-9a28-98e35ef00a12",
    "email": "user@example.com",
    "full_name": "Anish Naziran",
    "is_active": true,
    "created_at": "2026-07-23T21:00:00Z"
  }
  ```

---

### `POST /auth/login`
Authenticates user credentials and returns JWT token pair.

* **Request Body** (`application/x-www-form-urlencoded`):
  * `username`: `user@example.com`
  * `password`: `SecurePassword123!`
* **Response** (`200 OK`):
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "refresh_token": "d98e1f...",
    "token_type": "bearer"
  }
  ```

---

### `POST /auth/refresh`
Rotates and issues a new access/refresh token pair.

* **Request Body** (`application/json`):
  ```json
  {
    "refresh_token": "d98e1f..."
  }
  ```

---

### `POST /auth/logout`
Revokes the current active session.

* **Headers**: `Authorization: Bearer <access_token>`
* **Response** (`200 OK`): `{"message": "Successfully logged out"}`

---

## 2. Resume & ATS Scoring Endpoints (`/api/v1/resumes`)

### `POST /resumes/upload`
Uploads a resume file (PDF or DOCX), executes text extraction, calculates ATS compatibility score, and saves analysis.

* **Headers**: `Authorization: Bearer <access_token>`
* **Request Format**: `multipart/form-data`
  * `file`: Binary file (`.pdf`, `.docx`)
  * `target_job_description` (optional): Plaintext job description string.
* **Response** (`201 Created`):
  ```json
  {
    "id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "file_name": "Anish_Resume.pdf",
    "file_url": "/uploads/9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d.pdf",
    "file_size": 124500,
    "analysis": {
      "ats_score": 82,
      "feedback": {
        "score_breakdown": {
          "contact_info": 10,
          "structure": 20,
          "skills": 25,
          "impact_metrics": 15,
          "readability": 12
        },
        "suggestions": [
          "Quantify project achievements with specific metrics (e.g. 'Boosted sales by 20%')."
        ]
      }
    }
  }
  ```

---

### `GET /resumes/my-resumes`
Retrieves all uploaded resumes for the authenticated user.

* **Headers**: `Authorization: Bearer <access_token>`
* **Response** (`200 OK`): Array of `ResumeResponse` objects.

---

### `POST /resumes/{resume_id}/rescore`
Re-evaluates an existing resume against a newly provided target job description.

* **Headers**: `Authorization: Bearer <access_token>`
* **Request Body** (`application/json`):
  ```json
  {
    "target_job_description": "We are seeking a Business Analyst proficient in SQL, Tableau, Jira, and stakeholder management..."
  }
  ```
* **Response** (`200 OK`): Updated `ResumeResponse` object.

---

### `DELETE /resumes/{resume_id}`
Soft deletes a resume and removes raw file storage.

* **Headers**: `Authorization: Bearer <access_token>`
* **Response** (`200 OK`): `{"success": true, "message": "Resume deleted successfully."}`

---

### `GET /resumes/{resume_id}/report`
Generates and downloads a PDF evaluation report for a resume analysis.

* **Headers**: `Authorization: Bearer <access_token>`
* **Response** (`200 OK`): Binary `application/pdf` stream.

---

### `GET /resumes/{resume_id}/recommendations`
Returns personalized career development steps, skill gap analysis, recommended certifications, and online courses.

* **Headers**: `Authorization: Bearer <access_token>`
* **Response** (`200 OK`):
  ```json
  {
    "gap_analysis": {
      "Business Analyst": {
        "match_percentage": 85,
        "matching_skills": ["Sql", "Excel", "Jira", "User Stories"],
        "missing_skills": ["Tableau", "Brd"]
      }
    },
    "roadmap": {
      "target_role": "Business Analyst",
      "skill_gap_summary": "Your profile matches 85% of standard skills for a Business Analyst.",
      "steps": [
        "Master drafting BRDs/FRDs and detailed user stories in Jira",
        "Build interactive executive dashboards using Tableau or Power BI"
      ]
    },
    "certifications": ["CBAP (Certified Business Analysis Professional)"],
    "courses": ["Business Analysis Fundamentals (Udemy)"]
  }
  ```

---

## 3. RAG AI Chatbot Endpoints (`/api/v1/chatbot`)

### `POST /chatbot/upload`
Uploads reference PDF/DOCX context documents and triggers background vector embedding generation (`pgvector`).

* **Headers**: `Authorization: Bearer <access_token>`
* **Request Format**: `multipart/form-data`
  * `file`: Binary context file (`.pdf`, `.docx`, `.txt`)
* **Response** (`202 Accepted`): `{"message": "Document uploaded. Embeddings generated in background."}`

---

### `POST /chatbot/sessions`
Creates a new RAG chat conversation session.

* **Headers**: `Authorization: Bearer <access_token>`
* **Request Body** (`application/json`):
  ```json
  {
    "title": "Career Strategy Session"
  }
  ```

---

### `POST /chatbot/sessions/{session_id}/stream`
Streams Server-Sent Events (SSE) responses using RAG retrieval + Gemini LLM synthesis.

* **Headers**: `Authorization: Bearer <access_token>`
* **Request Body** (`application/x-www-form-urlencoded`):
  * `content`: User prompt string
* **Response** (`text/event-stream`): Streaming SSE JSON tokens:
  ```http
  data: {"token": "Based "}
  data: {"token": "on your "}
  data: {"done": true, "citations": ["Resume.pdf"], "confidence_score": 0.94}
  ```
