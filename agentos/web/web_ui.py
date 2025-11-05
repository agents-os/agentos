#!/usr/bin/env python3
"""
AgentOS Web UI - Simple web interface for managing agents
"""

import os
from pathlib import Path

from flask import Flask

# Find project root (where templates/ and static/ are located)
project_root = Path(__file__).parent.parent.parent
template_folder = project_root / 'templates'
static_folder = project_root / 'static'

app = Flask(__name__, 
            template_folder=str(template_folder),
            static_folder=str(static_folder))
app.secret_key = os.environ.get('AGENTOS_SECRET_KEY', 'agentos-secret-key-change-in-production')

app.config['JSON_SORT_KEYS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

from agentos.web.web_routes import register_routes
register_routes(app)


if __name__ == '__main__':
    templates_dir = Path(__file__).parent / 'templates'
    templates_dir.mkdir(exist_ok=True)
    
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    
    print("🌐 Starting AgentOS Web UI...")
    print(f"📍 Access at: http://localhost:5000")
    print(f"🔧 Mode: {'Development' if debug_mode else 'Production'}")
    print(f"🏥 Health check: http://localhost:5000/health")
    print(f"📊 Metrics: http://localhost:5000/metrics")
    
    app.run(host='0.0.0.0', port=5000, debug=debug_mode, threaded=True)
