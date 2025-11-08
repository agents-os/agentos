# AgentOS Production Deployment Guide

## Prerequisites

- Python 3.8+
- Docker & Docker Compose (for containerized deployment)
- Nginx (for reverse proxy)
- Systemd (for service management)

## Deployment Options

### Option 1: Docker Compose (Recommended)

1. **Set up environment variables**:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
nano .env
```

Required variables:
```bash
AGENTOS_SECRET_KEY=your-secure-random-key-here
GIT_HUB_TOKEN=your-github-token  # Or other LLM provider keys
FLASK_ENV=production
```

2. **Deploy with Docker Compose**:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

3. **Check health**:
```bash
curl http://localhost:5000/health
```

4. **View logs**:
```bash
docker-compose -f docker-compose.prod.yml logs -f
```

### Option 2: Systemd Service

1. **Create dedicated user**:
```bash
sudo useradd -r -s /bin/false agentos
sudo mkdir -p /opt/agentos /var/log/agentos
sudo chown agentos:agentos /opt/agentos /var/log/agentos
```

2. **Install AgentOS**:
```bash
cd /opt/agentos
sudo -u agentos python3 -m venv venv
sudo -u agentos venv/bin/pip install -r requirements.txt
```

3. **Configure environment**:
```bash
sudo mkdir -p /etc/agentos
sudo nano /etc/agentos/agentos.env
```

Add:
```bash
AGENTOS_SECRET_KEY=your-secure-random-key
GIT_HUB_TOKEN=your-token
FLASK_ENV=production
AGENTOS_LOG_LEVEL=INFO
```

4. **Install systemd service**:
```bash
sudo cp agentos.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable agentos
sudo systemctl start agentos
```

5. **Check status**:
```bash
sudo systemctl status agentos
sudo journalctl -u agentos -f
```

### Option 3: Manual with Gunicorn

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Set environment variables**:
```bash
export FLASK_ENV=production
export AGENTOS_SECRET_KEY=your-key
export GIT_HUB_TOKEN=your-token
```

3. **Run with Gunicorn**:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log \
  web_ui:app
```

## Nginx Reverse Proxy Setup

1. **Install Nginx**:
```bash
sudo apt install nginx  # Ubuntu/Debian
sudo yum install nginx  # CentOS/RHEL
```

2. **Configure Nginx**:
```bash
sudo cp nginx.conf /etc/nginx/sites-available/agentos
sudo ln -s /etc/nginx/sites-available/agentos /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

3. **SSL/TLS Setup** (recommended):
```bash
# Using Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## Monitoring & Observability

### Health Checks

```bash
# Basic health check
curl http://localhost:5000/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00",
  "database": "connected",
  "scheduler": "running",
  "agents_count": 5
}
```

### Metrics

Prometheus-compatible metrics available at `/metrics`:

```bash
curl http://localhost:5000/metrics
```

### Logging

Logs are stored in:
- Application logs: `~/.agentos/logs/agentos.log`
- Agent logs: `~/.agentos/logs/<agent_name>_<id>.log`
- Web server logs: `/var/log/agentos/` (systemd) or Docker volumes

View logs:
```bash
# Systemd
sudo journalctl -u agentos -f

# Docker
docker-compose logs -f agentos

# Direct
tail -f ~/.agentos/logs/agentos.log
```

## Security Hardening

### 1. Environment Variables
Never commit `.env` files. Use secure secret management:
```bash
# Generate secure secret key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Firewall Configuration
```bash
# Allow only necessary ports
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 3. Rate Limiting
Nginx configuration includes rate limiting:
- API endpoints: 10 req/s
- General pages: 30 req/s

### 4. Database Security
- SQLite database is stored in `~/.agentos/runtime.db`
- Ensure proper file permissions: `chmod 600 ~/.agentos/runtime.db`

### 5. Command Filtering
AgentOS blocks destructive commands by default. Review `utils.py` for the list.

## Performance Tuning

### Gunicorn Workers
```bash
# Formula: (2 x CPU cores) + 1
gunicorn -w 9 -b 0.0.0.0:5000 web_ui:app  # For 4 CPU cores
```

### Database Optimization
SQLite is configured with WAL mode for better concurrency:
```python
# Automatically enabled in db.py
PRAGMA journal_mode=WAL
```

### Resource Limits
Docker Compose includes resource limits:
- CPU: 2 cores max
- Memory: 2GB max

Adjust in `docker-compose.prod.yml` as needed.

## Backup & Recovery

### Database Backup
```bash
# Backup SQLite database
cp ~/.agentos/runtime.db ~/.agentos/runtime.db.backup

# Automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
cp ~/.agentos/runtime.db ~/.agentos/backups/runtime_$DATE.db
find ~/.agentos/backups -mtime +7 -delete  # Keep 7 days
```

### Log Rotation
```bash
# Configure logrotate
sudo nano /etc/logrotate.d/agentos
```

Add:
```
/var/log/agentos/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 agentos agentos
    sharedscripts
    postrotate
        systemctl reload agentos > /dev/null 2>&1 || true
    endscript
}
```

## Troubleshooting

### Service won't start
```bash
# Check logs
sudo journalctl -u agentos -n 50

# Check configuration
python3 production_config.py

# Verify dependencies
pip list | grep -E "flask|gunicorn|pyyaml"
```

### Database locked errors
```bash
# Check for stale connections
lsof ~/.agentos/runtime.db

# Restart service
sudo systemctl restart agentos
```

### High memory usage
```bash
# Check running agents
agentos ps

# Prune stopped agents
agentos prune

# Monitor resources
docker stats agentos-prod  # Docker
top -p $(pgrep -f gunicorn)  # Systemd
```

### API timeouts
- Increase timeout in `nginx.conf`
- Increase Gunicorn timeout: `--timeout 180`
- Check LLM provider API status

## Scaling

### Horizontal Scaling
For high availability, deploy multiple instances behind a load balancer:

```yaml
# docker-compose.scale.yml
services:
  agentos:
    deploy:
      replicas: 3
```

### Load Balancer
Use Nginx, HAProxy, or cloud load balancers (AWS ALB, GCP Load Balancer).

### Database Considerations
SQLite is suitable for single-instance deployments. For multi-instance:
- Consider PostgreSQL or MySQL
- Implement distributed locking
- Use Redis for session management

## Maintenance

### Updates
```bash
# Docker
docker-compose pull
docker-compose up -d

# Systemd
cd /opt/agentos
sudo -u agentos git pull
sudo -u agentos venv/bin/pip install -r requirements.txt
sudo systemctl restart agentos
```

### Health Monitoring
Set up monitoring with:
- Prometheus + Grafana
- Datadog
- New Relic
- CloudWatch (AWS)

Example Prometheus scrape config:
```yaml
scrape_configs:
  - job_name: 'agentos'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/metrics'
```

## Support

- Purchase: https://junaidahmed65.gumroad.com/l/spfzuo
- Repository: https://github.com/agents-os/agentos
- Issues: https://github.com/agents-os/agentos/issues
