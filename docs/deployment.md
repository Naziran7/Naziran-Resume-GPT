# Production Deployment Guide

This document describes the steps required to deploy **NaziranGPT** to standard cloud platforms.

---

## 🏗️ Deployment Strategy

- **Frontend**: Hosted on **Vercel** as a high-performance static React Single Page Application (SPA).
- **Backend**: Hosted on **Render** (or equivalent PaaS) as a Python/FastAPI web service container.
- **Database**: Hosted on **Neon** or **Supabase** as a fully managed PostgreSQL database with the `pgvector` extension enabled.
- **Cache**: Hosted on **Render Redis** (or equivalent cloud Redis instance).

---

## 1. Managed Database Setup (Neon / Supabase)

1. **Create Database**: Sign up at [Neon](https://neon.tech) or [Supabase](https://supabase.com) and spin up a new PostgreSQL database instance.
2. **Enable Vector Extensions**:
   Navigate to the SQL Editor in your database console and execute:

   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

3. **Retrieve Database URL**: Copy the connection string. It will look like:
   `postgresql://[user]:[password]@[host]/[dbname]?sslmode=require`

---

## 2. Backend Deployment (Render)

1. **Log in to Render**: Connect your GitHub repository.
2. **Create Web Service**:
   - Select **Web Service**.
   - Connect your NaziranGPT project repository.
   - Set the build configuration:
     - **Environment**: `Docker`
     - **Dockerfile Path**: `backend/Dockerfile`
3. **Configure Environment Variables**:
   Add the following variables in the Render environment panel:
   - `ENVIRONMENT` = `production`
   - `DATABASE_URL` = *Your Neon/Supabase PostgreSQL connection URL*
   - `SECRET_KEY` = *Generate a secure key via `openssl rand -hex 32`*
   - `GEMINI_API_KEY` = *Your Google Gemini API Key*
   - `REDIS_HOST` = *Your Render Redis hostname (or internal connection URL)*
4. **Deploy**: Trigger the deploy. Render will compile your Docker image, apply migrations (`alembic upgrade head`), and boot the server.

---

## 3. Frontend Deployment (Vercel)

1. **Log in to Vercel**: Connect your GitHub repository.
2. **Import Project**:
   - Import the NaziranGPT repository.
   - Configure the workspace sub-directory:
     - **Root Directory**: `frontend`
3. **Vite Framework Settings**:
   - Vercel automatically detects the Vite builder settings.
   - Ensure the **Build Command** is `npm run build` and the **Output Directory** is `dist`.
4. **Environment Variables**:
   Add the following environment variable:
   - `VITE_API_URL` = *Your Render Backend Live URL (e.g. `https://nazirangpt-backend.onrender.com/api/v1`)*
5. **Client-Side Routing Support**:
   The custom `vercel.json` already present inside our `frontend` folder handles route rewrites so React Router handles URL page refreshes correctly.
6. **Deploy**: Click **Deploy**. Vercel will bundle the frontend assets and distribute them across their edge network.
