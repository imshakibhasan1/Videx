# Videx — AI Video Reverse-Engineer (Free)

> [!NOTE]
> **What is Videx?**
> This is a video prompt generation app. You upload a video, and this app will give you a text-to-video prompt exactly like your given video. You can also add more creative value and modify the video visuals before generating the final prompt!

## 🚀 Features
- **Video Analysis (Step 1)**: Upload a video to have the MiMo AI engine extract physical properties, technical metadata, scene summaries, and style options.
- **Detractor Engine (Step 3)**: Select styles, frame rates, aspect ratios, and durations to generate a highly detailed, cinematic prompt.
- **Real-time Updates**: Server-Sent Events (SSE) keep the UI updated in real-time as background processing happens.
- **Full Stack Architecture**: Next.js 14 frontend, FastAPI backend, PostgreSQL, Redis, and Celery for background tasks.

## 🛠 Tech Stack
- **Frontend**: Next.js (React), Tailwind CSS, TypeScript
- **Backend**: Python 3.12, FastAPI, SQLAlchemy (asyncpg)
- **Database / Cache**: PostgreSQL 16, Redis 7
- **Task Queue**: Celery (running in Docker)
- **Third-Party APIs**: Cloudinary (Video hosting), OpenCode/MiMo V2.5 API

## 📋 Prerequisites
Make sure you have the following installed on your machine:
- [Docker & Docker Desktop](https://www.docker.com/) (Must be running)
- [Node.js](https://nodejs.org/en/) (v18+ recommended)
- Git

## ⚙️ Setup Instructions

### 1. Clone the repository
```bash
git clone <your-github-repo-url>
cd Videx
```

### 2. Configure Environment Variables
You need to set up `.env` files for both the frontend and backend. 
*(Note: Do not commit `.env` files to GitHub!)*

# Instruction:
<h4>🔑 How to Get Configuration Credentials </h4>
<p> To get your Cloudinary cloud profile configurations for both frontend and backend signatures:</p>
<ul>
<li>Visit Cloudinary Website and click on Sign Up for Free or Login.</li>
<li>Once logged in and inside your main dashboard console, look at the Product Environment Credentials card right on the home interface.</li>
<li>Copy the following variables and put them inside your backend .env and frontend .env </li>
<li>Cloud Name: (Maps to CLOUDINARY_CLOUD_NAME on backend and NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME on frontend).</li>
<li>API Key: (Maps to CLOUDINARY_API_KEY).</li>
<li> API Secret: (Maps to CLOUDINARY_API_SECRET).</li>
<li>Optional Optimization: Go to Settings -> Upload Settings and verify your unsigned/signed presets if you plan to configure manual unsigned fallback profiles.</li>
</ul>

<h4>🔑 MiMo V2.5 API Key (OpenCode AI Engine)</h4>
<p>To connect the backend automation worker to the multi-modal video breakdown nodes via the OpenCode gateway:</p>
<ul>
<li>Navigate directly to OpenCode AI and register an account or sign in via Google/GitHub.</li>
<li>Go to your user profile settings dashboard or look for the API Keys / Tokens panel from the main sidebar.</li>
<li> Click on Create New Secret Key, assign a descriptive name (e.g., Videx-Dev-Key), and click Generate.</li>
<li>Copy the token immediately (it will look like sk-...) and save it to your backend .env file under MIMO_API_KEY.</li>
<li> Ensure your endpoint targets point to the standardized completions path as defined below:</li>
<li> URL: https://opencode.ai/zen/v1/chat/completions </li>
<li> Model Identifier: mimo-v2.5-free </li>
</ul>


**Backend (`videx-backend/.env`)**
Create a `.env` file in the `videx-backend` directory with the following variables:
```env
APP_NAME=VIDEX
DEBUG=false
SECRET_KEY=<generate_a_random_secret_string>
ALLOWED_ORIGINS=["http://localhost:3000"]

# Database & Redis (Matches docker-compose defaults)
DATABASE_URL=postgresql+asyncpg://videx_user:videx_pass@db:5432/videx_db
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# Cloudinary Credentials
CLOUDINARY_CLOUD_NAME=<your_cloudinary_cloud_name>
CLOUDINARY_API_KEY=<your_cloudinary_api_key>
CLOUDINARY_API_SECRET=<your_cloudinary_api_secret>
CLOUDINARY_MAX_BYTES=52428800
CLOUDINARY_MAX_DURATION=15

# MiMo API
MIMO_API_KEY=<your_mimo_api_key>
MIMO_API_URL=https://opencode.ai/zen/v1/chat/completions
MIMO_MODEL=mimo-v2.5-free
MIMO_MAX_TOKENS=2048
MIMO_TIMEOUT=120.0
MIMO_FPS=2

# JWT & Auth
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
```

**Frontend (`videx-frontend/.env`)**
Create a `.env` file in the `videx-frontend` directory:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME=<your_cloudinary_cloud_name>
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

### 3. Start the Backend Services (Docker)
Ensure Docker Desktop is running. The backend (FastAPI, Postgres, Redis, and Celery Worker) is entirely dockerized.

Open a terminal and run:
```bash
cd videx-backend/docker
docker compose up -d
```
*Note: This will spin up the database, cache, API on port 8000, and the background worker in detached mode.*

### 4. Start the Frontend
In a new terminal window, install dependencies and start the Next.js development server:

```bash
cd videx-frontend
npm install
npm run dev
```

### 5. Open in Browser
Once both the backend and frontend are running, navigate to:
👉 [http://localhost:3000](http://localhost:3000)

## 🏗 Architecture Notes
- The system uses Celery background tasks to handle the slow API calls to the MiMo AI engine, preventing HTTP timeouts.
- Real-time communication between Celery and the Frontend is achieved via Redis Pub/Sub connected to a FastAPI Server-Sent Events (SSE) endpoint.
