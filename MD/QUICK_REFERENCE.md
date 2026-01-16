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

### Security Validation

```python
from agentos.core.security import validate_command, validate_input

# Check command safety
result = validate_command("rm -rf /")
print(result.is_safe)  # False

# Check input for injection
result = validate_input("hello; whoami")
print(result.is_safe)  # False
```

### Resource Limits

```yaml
# In manifest or default.yaml
resource_limits:
  max_steps: 50
  timeout: 300
  max_memory_mb: 512
  max_cpu_percent: 50
```

## 🔄 Retry Configuration

```yaml
retry_config:
  max_retries: 3
  initial_delay: 1.0
  max_delay: 30.0
  exponential_base: 2.0
  jitter: true
```

```python
from agentos.core.retry import retry_with_backoff, DEFAULT_LLM_RETRY

@retry_with_backoff(DEFAULT_LLM_RETRY)
def call_api():
    return api.request()
```

## 💾 Chat History

```python
from agentos.core.chat_history import ChatHistoryManager

history = ChatHistoryManager()
conv_id = history.create_conversation(agent_id="assistant")
history.add_message(conv_id, "user", "Hello!")
history.export_conversation(conv_id, "chat.md", format="markdown")
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
