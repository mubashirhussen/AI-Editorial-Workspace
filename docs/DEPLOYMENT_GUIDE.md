# AI Editorial Workspace — Production Deployment Guide

This guide details steps for deploying the AI Editorial Workspace to containerized, cloud, or self-hosted environments.

---

## 1. Quick Start: Docker Compose Deployment

The fastest way to deploy the complete stack (PostgreSQL + FastAPI Backend + Nginx/React Frontend):

### Step 1: Clone Repository & Create Environment Configuration
```bash
git clone https://github.com/mubashirhussen/AI-Editorial-Workspace.git
cd AI-Editorial-Workspace
cp .env.example .env
```

Ensure `.env` contains your production settings:
```env
# Core Security
SECRET_KEY=generate_a_random_64_character_hex_secret_here
ENVIRONMENT=production
TESTING=False

# Database (Leave as postgresql for docker-compose)
DATABASE_URL=postgresql://editorial_user:editorial_secret_pass@db:5432/editorial_workspace
POSTGRES_USER=editorial_user
POSTGRES_PASSWORD=editorial_secret_pass
POSTGRES_DB=editorial_workspace

# Optional AI Provider API Keys (Can also be added via Settings UI)
GROQ_API_KEY=gsk_...
OPENAI_API_KEY=sk-...
```

### Step 2: Build & Launch Containers
```bash
docker compose up -d --build
```

### Step 3: Verify Container Health
```bash
docker compose ps
```
Both `editorial-backend` and `editorial-frontend` should show `healthy` status.

Access the application:
- **Frontend Workspace:** [http://localhost](http://localhost) (Port 80)
- **Backend API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs) (Port 8000)
- **Health Probe:** [http://localhost:8000/health/live](http://localhost:8000/health/live)

---

## 2. Manual / Self-Hosted Production Deployment

### Backend Setup (Ubuntu 22.04 LTS / Debian 12)

1. **Install Prerequisites:**
   ```bash
   sudo apt update && sudo apt install -y python3.11 python3.11-venv python3-pip postgresql nginx
   ```

2. **Configure PostgreSQL:**
   ```bash
   sudo -u postgres psql -c "CREATE USER editorial_user WITH PASSWORD 'strong_db_password';"
   sudo -u postgres psql -c "CREATE DATABASE editorial_workspace OWNER editorial_user;"
   ```

3. **Install Application:**
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Run Migrations:**
   ```bash
   export PYTHONPATH=.
   export DATABASE_URL="postgresql://editorial_user:strong_db_password@localhost:5432/editorial_workspace"
   alembic -c backend/alembic.ini upgrade head
   ```

5. **Configure Systemd Service (`/etc/systemd/system/editorial-backend.service`):**
   ```ini
   [Unit]
   Description=AI Editorial Workspace FastAPI Backend
   After=network.target postgresql.service

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/var/www/AI-Editorial-Workspace
   Environment="PYTHONPATH=/var/www/AI-Editorial-Workspace"
   EnvironmentFile=/var/www/AI-Editorial-Workspace/.env
   ExecStart=/var/www/AI-Editorial-Workspace/venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --workers 4
   Restart=always
   RestartSec=5

   [Install]
   WantedBy=multi-user.target
   ```

6. **Start Backend:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now editorial-backend
   ```

---

## 3. Frontend Build & Nginx Hosting

1. **Build Static Assets:**
   ```bash
   cd frontend
   npm ci
   npm run build
   # Assets output to frontend/dist
   ```

2. **Nginx Site Configuration (`/etc/nginx/sites-available/editorial`):**
   ```nginx
   server {
       listen 80;
       server_name editorial.yourdomain.com;
       root /var/www/AI-Editorial-Workspace/frontend/dist;
       index index.html;

       location /api/ {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }

       location /health {
           proxy_pass http://127.0.0.1:8000/health;
       }

       location / {
           try_files $uri $uri/ /index.html;
       }
   }
   ```

3. **Enable & Secure with Let's Encrypt:**
   ```bash
   sudo ln -s /etc/nginx/sites-available/editorial /etc/nginx/sites-enabled/
   sudo nginx -t && sudo systemctl reload nginx
   sudo certbot --nginx -d editorial.yourdomain.com
   ```

---

## 4. Cloud Platform Deployments (Render / Railway / Fly.io)

### Render / Railway
- Deploy `backend/Dockerfile` as a Web Service.
- Set environment variables: `DATABASE_URL` (from attached managed PostgreSQL), `SECRET_KEY`, `ENVIRONMENT=production`.
- Deploy `frontend/Dockerfile` or Static Site using `frontend/dist`.

### Fly.io
- Deploy using root `fly.toml`:
  ```toml
  app = "editorial-workspace"
  primary_region = "iad"

  [build]
    dockerfile = "backend/Dockerfile"

  [http_service]
    internal_port = 8000
    force_https = true
    auto_stop_machines = true
    auto_start_machines = true
    min_machines_running = 1
  ```
