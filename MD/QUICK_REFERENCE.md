# AgentOS Production Quick Reference

## 🚀 Deployment

### Docker (Recommended)
```bash
cp .env.example .env          # Configure
make docker-prod              # Deploy
make health-check             # Verify
```

### Systemd
```bash
make install-service          # Install
sudo systemctl start agentos  # Start
make status                   # Check
```

## 📊 Monitoring

```bash
# Health check
curl http://localhost:5000/health

# Metrics
curl http://localhost:5000/metrics

# Monitor agents
make monitor

# View logs
make logs-service             # Systemd
make docker-prod-logs         # Docker
```

## 🔧 Management

```bash
# List agents
agentos ps

# View logs
agentos logs <agent-id>

# Stop agent
agentos stop <agent-id>

# Clean up
agentos prune

# Backup database
make backup-db
```

## 🔒 Security

### Required Environment Variables
```bash
AGENTOS_SECRET_KEY=<random-key>
GIT_HUB_TOKEN=<your-token>     # Or other LLM provider
FLASK_ENV=production
```

### Generate Secret Key
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 🆘 Troubleshooting

### Service Issues
```bash
python3 startup_check.py      # Validate config
make logs-service             # Check logs
sudo systemctl restart agentos # Restart
```

### Database Issues
```bash
lsof ~/.agentos/runtime.db    # Check locks
make backup-db                # Backup
make restore-db               # Restore
```

### Performance Issues
```bash
agentos ps                    # Check agents
agentos prune                 # Clean up
docker stats agentos-prod     # Monitor resources
```

## 📈 Endpoints

- **Web UI**: `http://localhost:5000`
- **Health**: `http://localhost:5000/health`
- **Metrics**: `http://localhost:5000/metrics`
- **API**: `http://localhost:5000/api/*`

## 🎯 Production Checklist

- [ ] Set secure `AGENTOS_SECRET_KEY`
- [ ] Configure LLM API key
- [ ] Set `FLASK_ENV=production`
- [ ] Configure Nginx/reverse proxy
- [ ] Set up SSL/TLS
- [ ] Configure firewall
- [ ] Set up log rotation
- [ ] Configure backups
- [ ] Set up monitoring
- [ ] Test health checks

## 📞 Support

- **Docs**: `DEPLOYMENT.md`
- **Config**: `.env.example`
- **Commands**: `make help`
