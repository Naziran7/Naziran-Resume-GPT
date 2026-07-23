# Database Schema Documentation

This document describes the PostgreSQL database schema for the NaziranGPT MVP.

---

## 📊 Entity Relationship Diagram

```mermaid
erDiagram
    ROLES ||--o{ USERS : "defines rights for"
    USERS ||--o{ USER_SESSIONS : "owns"
    USERS ||--o{ RESUMES : "uploads"
    RESUMES ||--|| RESUME_ANALYSES : "evaluates to"
    RESUMES ||--o{ SKILLS : "contains"
    RESUMES ||--o{ EDUCATION : "outlines"
    RESUMES ||--o{ EXPERIENCE : "details"
    RESUMES ||--o{ CERTIFICATIONS : "lists"

    ROLES {
        uuid id PK
        string name UK
        string description
        datetime created_at
    }

    USERS {
        uuid id PK
        string email UK
        string hashed_password
        string full_name
        uuid role_id FK
        boolean is_active
        datetime created_at
        datetime updated_at
        datetime deleted_at
    }

    USER_SESSIONS {
        uuid id PK
        uuid user_id FK
        string refresh_token
        datetime expires_at
        boolean is_revoked
        string client_ip
        string user_agent
        datetime created_at
    }

    RESUMES {
        uuid id PK
        uuid user_id FK
        string file_name
        string file_url
        integer file_size
        text raw_text
        datetime created_at
        datetime updated_at
        datetime deleted_at
    }

    RESUME_ANALYSES {
        uuid id PK
        uuid resume_id FK
        integer ats_score
        json feedback
        json extracted_data
        datetime created_at
        datetime updated_at
        datetime deleted_at
    }

    SKILLS {
        uuid id PK
        uuid resume_id FK
        string name
        string category
        datetime created_at
    }

    EDUCATION {
        uuid id PK
        uuid resume_id FK
        string institution
        string degree
        string field_of_study
        string start_date
        string end_date
        text description
        datetime created_at
    }

    EXPERIENCE {
        uuid id PK
        uuid resume_id FK
        string company
        string position
        string location
        string start_date
        string end_date
        text description
        datetime created_at
    }

    CERTIFICATIONS {
        uuid id PK
        uuid resume_id FK
        string name
        string issuing_organization
        string issue_date
        string expiration_date
        datetime created_at
    }
```

---

## 🔑 Database Design Principles Implemented

1. **UUID Primary Keys**: All records use random UUIDs for key identification. This prevents sequential enumeration attacks and eases future database splits or replication.
2. **Cascade Restrictions**: Users and Resumes are protected by cascading rules. Session records cascade delete when users are purged, but delete operations on standard files trigger soft deletes to keep historical data intact.
3. **Soft Deletes**: Tables for `users`, `resumes`, and `resume_analyses` include a `deleted_at` field. Database requests check for null values on this field, enabling data recovery capabilities.
4. **Foreign Key Indexing**: All foreign keys (`role_id`, `user_id`, `resume_id`) are indexed to speed up relational lookup and join queries under high load.
