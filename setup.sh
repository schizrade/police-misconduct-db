#!/bin/bash
# =========================================================
# Police Misconduct Database - Ubuntu Server Setup Script
# Tested on Ubuntu 22.04 LTS / 24.04 LTS
# Run as root: sudo bash setup.sh
# =========================================================

set -e

# ---------- Colour helpers ----------
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()    { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
err_exit(){ echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# ---------- Root check ----------
[ "$EUID" -ne 0 ] && err_exit "Please run as root: sudo bash setup.sh"

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
info "Working directory: $APP_DIR"

echo ""
echo "========================================================="
echo "  Police Misconduct Database - Enhanced v2.0"
echo "  Ubuntu Server Setup"
echo "========================================================="
echo ""

# ==========================================================
# STEP 1 — System packages
# ==========================================================
info "Step 1: Updating apt and installing system dependencies..."

apt update -qq
apt install -y \
    curl wget gnupg lsb-release ca-certificates \
    python3 python3-venv python3-dev python3-pip \
    postgresql postgresql-contrib \
    nginx \
    libpq-dev \
    build-essential \
    libmagic1 \
    openssl \
    ufw

# ---------- Node.js 18 LTS via NodeSource ----------
info "Installing Node.js 18 LTS..."
if ! command -v node &>/dev/null || [ "$(node -e 'process.exit(parseInt(process.version.slice(1)) < 18 ? 1 : 0)'; echo $?)" = "1" ]; then
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - 2>/dev/null
    apt install -y nodejs
else
    info "Node.js $(node --version) already installed, skipping."
fi

info "Installed versions:"
echo "  Python : $(python3.11 --version)"
echo "  Node   : $(node --version)"
echo "  npm    : $(npm --version)"
echo "  nginx  : $(nginx -v 2>&1)"
echo "  psql   : $(psql --version)"

# ==========================================================
# STEP 2 — PostgreSQL
# ==========================================================
info "Step 2: Configuring PostgreSQL..."

systemctl start postgresql
systemctl enable postgresql

echo ""
read -sp "  Enter a password for the database user 'misconduct_user': " DB_PASSWORD
echo ""
[ -z "$DB_PASSWORD" ] && err_exit "Database password cannot be empty."

sudo -u postgres psql <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'misconduct_user') THEN
    CREATE USER misconduct_user WITH ENCRYPTED PASSWORD '${DB_PASSWORD}';
  ELSE
    ALTER USER misconduct_user WITH ENCRYPTED PASSWORD '${DB_PASSWORD}';
  END IF;
END
\$\$;

DROP DATABASE IF EXISTS misconduct_db;
CREATE DATABASE misconduct_db OWNER misconduct_user;
GRANT ALL PRIVILEGES ON DATABASE misconduct_db TO misconduct_user;
SQL

sudo -u postgres psql -d misconduct_db -c "GRANT ALL ON SCHEMA public TO misconduct_user;"

info "Loading database schema..."
sudo -u postgres psql -U misconduct_user -d misconduct_db \
    -f "$APP_DIR/database/schema-enhanced.sql" \
    && info "Schema loaded successfully." \
    || err_exit "Schema load failed. Check database/schema-enhanced.sql."

# ==========================================================
# STEP 3 — Application system user
# ==========================================================
info "Step 3: Creating application system user..."
if ! id "misconduct" &>/dev/null; then
    useradd -r -m -s /bin/bash misconduct
    info "User 'misconduct' created."
else
    info "User 'misconduct' already exists."
fi

# ==========================================================
# STEP 4 — Backend (FastAPI)
# ==========================================================
info "Step 4: Setting up Python backend..."

BACKEND_DIR="$APP_DIR/backend"
cd "$BACKEND_DIR"

python3.11 -m venv venv
source venv/bin/activate

pip install --upgrade pip -q
pip install -r requirements.txt -q

# Generate secret key
SECRET_KEY=$(openssl rand -hex 32)

if [ ! -f .env ]; then
    cat > .env <<ENVEOF
# ---- Database ----
DATABASE_URL=postgresql://misconduct_user:${DB_PASSWORD}@localhost:5432/misconduct_db

# ---- Security ----
SECRET_KEY=${SECRET_KEY}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ---- API server ----
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False

# ---- CORS (add your server IP / domain after installing) ----
ALLOWED_ORIGINS=http://localhost:3000,http://localhost

# ---- App metadata ----
APP_NAME=Police Misconduct Database Enhanced
VERSION=2.0.0
ENVEOF
    info "backend/.env created."
else
    warn "backend/.env already exists — skipping generation."
fi

mkdir -p uploads
chmod 755 uploads

deactivate
cd "$APP_DIR"

# ==========================================================
# STEP 5 — Frontend (React)
# ==========================================================
info "Step 5: Setting up React frontend..."

FRONTEND_DIR="$APP_DIR/frontend"
cd "$FRONTEND_DIR"

npm install --loglevel=error

if [ ! -f .env ]; then
    cat > .env <<ENVEOF
# For production (traffic routed through Nginx /api/ proxy):
REACT_APP_API_URL=/api

# For local dev against the FastAPI server directly, use:
# REACT_APP_API_URL=http://localhost:8000
ENVEOF
    info "frontend/.env created."
fi

info "Building production frontend bundle..."
npm run build

cd "$APP_DIR"

# ==========================================================
# STEP 6 — File ownership
# ==========================================================
info "Step 6: Setting file ownership..."
chown -R misconduct:misconduct "$APP_DIR"
chmod -R 755 "$FRONTEND_DIR/build"

# ==========================================================
# STEP 7 — systemd service for FastAPI backend
# ==========================================================
info "Step 7: Creating systemd service for the backend..."

cat > /etc/systemd/system/misconduct-backend.service <<SVCEOF
[Unit]
Description=Police Misconduct Database API (FastAPI/uvicorn)
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=misconduct
Group=misconduct
WorkingDirectory=${BACKEND_DIR}
Environment="PATH=${BACKEND_DIR}/venv/bin"
EnvironmentFile=${BACKEND_DIR}/.env
ExecStart=${BACKEND_DIR}/venv/bin/python main.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=misconduct-backend

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload
systemctl enable misconduct-backend
systemctl start misconduct-backend
sleep 2
systemctl is-active --quiet misconduct-backend \
    && info "Backend service started successfully." \
    || warn "Backend service did not start — check: journalctl -u misconduct-backend"

# ==========================================================
# STEP 8 — Nginx
# ==========================================================
info "Step 8: Configuring Nginx..."

SERVER_IP=$(hostname -I | awk '{print $1}')

cat > /etc/nginx/sites-available/misconduct-db <<NGINXEOF
server {
    listen 80;
    server_name ${SERVER_IP} _;

    client_max_body_size 105M;

    location / {
        root ${FRONTEND_DIR}/build;
        index index.html;
        try_files \$uri \$uri/ /index.html;
    }

    location /api/ {
        proxy_pass         http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade \$http_upgrade;
        proxy_set_header   Connection 'upgrade';
        proxy_set_header   Host \$host;
        proxy_set_header   X-Real-IP \$remote_addr;
        proxy_set_header   X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout    300;
        proxy_connect_timeout 300;
        proxy_send_timeout    300;
    }

    location /uploads/ {
        alias ${BACKEND_DIR}/uploads/;
    }
}
NGINXEOF

rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/misconduct-db \
       /etc/nginx/sites-enabled/misconduct-db

nginx -t && systemctl restart nginx \
    && info "Nginx configured and restarted." \
    || err_exit "Nginx config test failed — check /etc/nginx/sites-available/misconduct-db"

# ==========================================================
# STEP 9 — UFW firewall
# ==========================================================
info "Step 9: Configuring UFW firewall..."
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable
info "Firewall rules applied (SSH + HTTP/HTTPS)."

# ==========================================================
# Done
# ==========================================================
echo ""
echo "========================================================="
echo -e "${GREEN}  Setup Complete!${NC}"
echo "========================================================="
echo ""
echo -e "  Application URL : ${YELLOW}http://${SERVER_IP}${NC}"
echo -e "  API docs        : ${YELLOW}http://${SERVER_IP}/api/docs${NC}"
echo ""
echo -e "${RED}  ⚠  DEFAULT ADMIN CREDENTIALS — CHANGE IMMEDIATELY:${NC}"
echo "     Username : admin"
echo "     Password : admin123"
echo ""
echo "  Useful commands:"
echo "    sudo systemctl status misconduct-backend"
echo "    sudo journalctl -u misconduct-backend -f"
echo "    sudo systemctl status nginx"
echo "    sudo nginx -t"
echo ""
echo "  To add your domain / SSL later, see QUICKSTART.md."
echo "========================================================="
