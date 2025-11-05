# AgentOS Development Makefile

.PHONY: help install dev test lint format clean build docker run-example

help: ## Show this help message
	@echo "AgentOS Development Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

dev: ## Install development dependencies
	pip install -r requirements.txt
	pip install pytest pytest-cov black flake8 pre-commit

test: ## Run tests
	pytest --cov=. --cov-report=term-missing

lint: ## Run linting
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

format: ## Format code
	black .

format-check: ## Check code formatting
	black --check .

clean: ## Clean up build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean ## Build package
	python setup.py sdist bdist_wheel

docker: ## Build Docker image
	docker build -t agentos:latest .

docker-run: ## Run Docker container
	docker run -it --rm agentos:latest

run-example: ## Run quick start example
	python agentos.py run examples/quick-start.yaml --task "create a hello world Python script"

demo: ## Run interactive demo
	@echo "🚀 AgentOS Demo"
	@echo "==============="
	python agentos.py --version
	python agentos.py ps
	@echo ""
	@echo "Try: make run-example"

setup-hooks: ## Setup pre-commit hooks
	pre-commit install

check-all: format-check lint test ## Run all checks

release: check-all build ## Prepare release
	@echo "✅ Ready for release!"
	@echo "📦 Built packages:"
	@ls -la dist/

# Production targets
validate: ## Validate production configuration
	python3 startup_check.py

start-prod: validate ## Start production server with gunicorn
	gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 \
		--access-logfile logs/access.log \
		--error-logfile logs/error.log \
		web_ui:app

docker-prod: ## Build and run production Docker setup
	docker-compose -f docker-compose.prod.yml up -d

docker-prod-logs: ## View production Docker logs
	docker-compose -f docker-compose.prod.yml logs -f

docker-prod-stop: ## Stop production Docker setup
	docker-compose -f docker-compose.prod.yml down

health-check: ## Check application health
	@curl -f http://localhost:5000/health || echo "❌ Health check failed"

metrics: ## View application metrics
	@curl -s http://localhost:5000/metrics

backup-db: ## Backup database
	@mkdir -p backups
	@cp ~/.agentos/runtime.db backups/runtime_$$(date +%Y%m%d_%H%M%S).db
	@echo "✅ Database backed up to backups/"

restore-db: ## Restore database from latest backup
	@cp $$(ls -t backups/runtime_*.db | head -1) ~/.agentos/runtime.db
	@echo "✅ Database restored from latest backup"

monitor: ## Monitor running agents
	watch -n 2 'python3 agentos.py ps'

security-scan: ## Run security scan
	@echo "Running security checks..."
	@pip install safety bandit
	@safety check
	@bandit -r . -ll

install-service: ## Install systemd service
	sudo cp agentos.service /etc/systemd/system/
	sudo systemctl daemon-reload
	sudo systemctl enable agentos
	@echo "✅ Service installed. Start with: sudo systemctl start agentos"

status: ## Check service status
	sudo systemctl status agentos

logs-service: ## View service logs
	sudo journalctl -u agentos -f