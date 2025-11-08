# AgentOS - Administrator Guide

## 📋 Table of Contents
- [System Overview](#system-overview)
- [Installation & Setup](#installation--setup)
- [Configuration](#configuration)
- [Database Management](#database-management)
- [Deployment](#deployment)
- [Monitoring & Maintenance](#monitoring--maintenance)
- [Security](#security)
- [Troubleshooting](#troubleshooting)
- [Backup & Recovery](#backup--recovery)

---

## 🎯 System Overview

AgentOS is a production-ready AI agent runtime system that manages, schedules, and executes AI agents with various LLM providers.

### Core Components
- **CLI Interface** - Command-line tools for agent management
- **Web UI** - Flask-based web interface (Port 5000)
- **Desktop App** - PyQt5-based desktop application
- **Database** - SQLite database for agent state management
- **Scheduler** - Background daemon for scheduled agent execution
- **Agent Executor** - Isolated execution environment for agents

### Architecture
```
agentos/
├── agent/          # Agent execution logic
├── cli/            # CLI commands and parsers
├── core/           # Core utilities (scheduler, config, isolation)
├── database/       # Database operations
├── llm/            # LLM provider integrations
└── web/            # Web UI and routes
```

---

## 🚀 Installation & Setup

### Prerequisites
```bash
# System Requirements
- Python 3.8+
- pip
- Virtual environment (recommended)
- 2GB RAM minimum
- 1GB disk space
```

### Installation Steps

1. **Clone Repository**
```bash
git clone https://github.com/agents-os/agentos
cd agentos
```

2. **Create Virtual Environment**
```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Install Package**
```bash
pip install -e .
```

5. **Verify Installation**
```bash
agentos --version
agentos --help
```

### Optional: Desktop App Dependencies
```bash
# For desktop application
pip install PyQtWebEngine pywebview

# Or system-wide (Ubuntu/Debian)
sudo apt install python3-pyqt5.qtwebengine
```

---

## ⚙️ Configuration

### Environment Variables

Create `.env` file in project root:
```bash
# Flask Configuration
FLASK_ENV=production
AGENTOS_SECRET_KEY=your-secret-key-here

# LLM Provider API Keys
GITHUB_TOKEN=ghp_xxxxxxxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
GOOGLE_API_KEY=xxxxxxxxxxxxx

# Database
DATABASE_PATH=~/.agentos/agents.db

# Logging
LOG_LEVEL=INFO
LOG_DIR=~/.agentos/logs
```

### Directory Structure
```bash
~/.agentos/
├── agents.db           # SQLite database
├── logs/              # Agent execution logs
│   └── agentos.log    # System log
└── prompts/           # Custom prompts (optional)
```

### Manifest Configuration

Default manifest location: `default.yaml`

```yaml
# Agent Configuration
name: my_assistant
model_provider: github  # github, openai, claude, gemini, ollama
model_version: openai/gpt-4o-mini
isolated: true

# Scheduling (Optional)
time: 14        # Daily at 14:00
repeat: 30      # Every 30 minutes

# Security
DESTRUCTIVE_COMMANDS:
  - rm
  - rmdir
  - sudo
  - dd
  - mkfs
  - format
```

---

## 💾 Database Management

### Database Location
```bash
~/.agentos/agents.db
```

### Database Schema

**agents** table:
- id (TEXT PRIMARY KEY)
- name (TEXT)
- model (TEXT)
- status (TEXT)
- pid (INTEGER)
- started_at (TEXT)
- completed_at (TEXT)
- log_path (TEXT)

**scheduled_agents** table:
- id (TEXT PRIMARY KEY)
- name (TEXT)
- manifest_path (TEXT)
- task (TEXT)
- schedule_type (TEXT)
- time_config (INTEGER)
- repeat_config (INTEGER)
- next_run (TEXT)
- created_at (TEXT)

### Database Operations

**Backup Database**
```bash
cp ~/.agentos/agents.db ~/.agentos/agents.db.backup
```

**Reset Database**
```bash
rm ~/.agentos/agents.db
# Database will be recreated on next run
```

**Query Database**
```bash
sqlite3 ~/.agentos/agents.db
sqlite> SELECT * FROM agents;
sqlite> SELECT * FROM scheduled_agents;
sqlite> .exit
```

**Prune Old Records**
```bash
agentos prune --force
```

---

## 🌐 Deployment

### Production Deployment

#### 1. Using Docker

**Build Image**
```bash
cd docker/
docker build -t agentos:latest -f Dockerfile ..
```

**Run Container**
```bash
docker run -d \
  --name agentos \
  -p 5000:5000 \
  -v ~/.agentos:/root/.agentos \
  -e GITHUB_TOKEN=your_token \
  agentos:latest
```

**Docker Compose**
```bash
cd docker/
docker-compose -f docker-compose.prod.yml up -d
```

#### 2. Using Systemd Service

**Create Service File**
```bash
sudo nano /etc/systemd/system/agentos.service
```

```ini
[Unit]
Description=AgentOS Service
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/AgentOS
Environment="PATH=/path/to/AgentOS/.venv/bin"
ExecStart=/path/to/AgentOS/.venv/bin/python agentos.py ui --host 0.0.0.0 --port 5000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and Start**
```bash
sudo systemctl daemon-reload
sudo systemctl enable agentos
sudo systemctl start agentos
sudo systemctl status agentos
```

#### 3. Using Nginx Reverse Proxy

**Nginx Configuration**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 📊 Monitoring & Maintenance

### Health Checks

**API Endpoint**
```bash
curl http://localhost:5000/health
```

**Response**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "database": "connected",
  "scheduler": "running",
  "agents_count": 5
}
```

### Metrics Endpoint

**Prometheus-style Metrics**
```bash
curl http://localhost:5000/metrics
```

### Log Management

**View System Logs**
```bash
tail -f ~/.agentos/logs/agentos.log
```

**View Agent Logs**
```bash
agentos logs <agent-id>
```

**Log Rotation**
```bash
# Add to crontab
0 0 * * * find ~/.agentos/logs -name "*.log" -mtime +30 -delete
```

### Performance Monitoring

**Check Running Agents**
```bash
agentos ps
```

**Monitor System Resources**
```bash
# CPU and Memory
ps aux | grep agentos

# Disk Usage
du -sh ~/.agentos/
```

### Scheduled Tasks

**View Scheduled Agents**
```bash
agentos schedule
```

**Scheduler Status**
```bash
# Check if scheduler is running
ps aux | grep scheduler
```

---

## 🔒 Security

### API Keys Management

**Never commit API keys to repository**
```bash
# Use .env file (already in .gitignore)
echo "GITHUB_TOKEN=your_token" >> .env
```

**Rotate Keys Regularly**
```bash
# Update .env file
# Restart service
sudo systemctl restart agentos
```

### Sandboxing

**Enable Isolation**
```yaml
# In manifest
isolated: true
```

**Blocked Commands**
```yaml
DESTRUCTIVE_COMMANDS:
  - rm
  - rmdir
  - sudo
  - dd
  - mkfs
  - format
  - shutdown
  - reboot
```

### Network Security

**Firewall Rules**
```bash
# Allow only specific IPs
sudo ufw allow from 192.168.1.0/24 to any port 5000
```

**HTTPS Setup**
```bash
# Use Let's Encrypt with Nginx
sudo certbot --nginx -d your-domain.com
```

### User Permissions

**Run as Non-Root User**
```bash
# Create dedicated user
sudo useradd -m -s /bin/bash agentos
sudo su - agentos
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Agent Won't Start
```bash
# Check logs
agentos logs <agent-id>

# Verify manifest
cat manifest.yaml

# Check API keys
echo $GITHUB_TOKEN
```

#### 2. Database Locked
```bash
# Kill hanging processes
pkill -f agentos

# Remove lock file
rm ~/.agentos/agents.db-journal
```

#### 3. Web UI Not Accessible
```bash
# Check if running
ps aux | grep agentos

# Check port
netstat -tulpn | grep 5000

# Restart service
sudo systemctl restart agentos
```

#### 4. Scheduler Not Running
```bash
# Check scheduler status
agentos schedule

# Restart with scheduler
agentos ui  # Scheduler starts automatically
```

#### 5. Ollama Connection Failed
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve
```

### Debug Mode

**Enable Verbose Logging**
```bash
agentos --verbose run manifest.yaml --task "your task"
```

**Check System Status**
```bash
./system_check.sh
```

---

## 💾 Backup & Recovery

### Backup Strategy

**Daily Backup Script**
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR=~/agentos-backups
DATE=$(date +%Y%m%d)

mkdir -p $BACKUP_DIR

# Backup database
cp ~/.agentos/agents.db $BACKUP_DIR/agents-$DATE.db

# Backup logs
tar -czf $BACKUP_DIR/logs-$DATE.tar.gz ~/.agentos/logs/

# Keep only last 7 days
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

**Add to Crontab**
```bash
crontab -e
# Add: 0 2 * * * /path/to/backup.sh
```

### Recovery

**Restore Database**
```bash
cp ~/agentos-backups/agents-20240101.db ~/.agentos/agents.db
```

**Restore Logs**
```bash
tar -xzf ~/agentos-backups/logs-20240101.tar.gz -C ~/
```

---

## 📞 Support & Maintenance

### Regular Maintenance Tasks

**Weekly**
- Review agent logs for errors
- Check disk space usage
- Verify scheduled agents are running

**Monthly**
- Update dependencies: `pip install -U -r requirements.txt`
- Rotate API keys
- Review and prune old agent records
- Backup database

**Quarterly**
- Security audit
- Performance optimization
- Update documentation

### System Updates

**Update AgentOS**
```bash
git pull origin main
pip install -U -r requirements.txt
sudo systemctl restart agentos
```

**Update Dependencies**
```bash
pip list --outdated
pip install -U <package-name>
```

---

## 📚 Quick Reference

### Essential Commands
```bash
# Start web UI
agentos ui --port 5000

# Run agent
agentos run manifest.yaml --task "your task"

# List agents
agentos ps

# View logs
agentos logs <agent-id>

# Stop agent
agentos stop <agent-id>

# Clean up
agentos prune --force

# View schedule
agentos schedule

# Remove schedule
agentos unschedule <schedule-id>
```

### File Locations
```
~/.agentos/agents.db          # Database
~/.agentos/logs/              # Logs
/etc/systemd/system/agentos.service  # Service file
docker/                       # Docker configs
```

### Important URLs
```
http://localhost:5000         # Web UI
http://localhost:5000/health  # Health check
http://localhost:5000/metrics # Metrics
```

---

## 📝 Notes

- Always test changes in development before production
- Keep API keys secure and rotate regularly
- Monitor disk space for logs and database
- Regular backups are critical
- Review security best practices periodically

---

**Version:** 1.0.0  
**Last Updated:** 2024  
**Maintained By:** AgentOS Team
