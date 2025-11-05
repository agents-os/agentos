"""Web UI Routes for AgentOS"""

import json
from datetime import datetime
from pathlib import Path

from flask import render_template, request, jsonify

from agentos.database import db
from agentos.core.scheduler import scheduler


def register_routes(app):
    """Register all routes with the Flask app"""

    @app.route('/')
    def dashboard():
        """Main dashboard showing agents and schedules"""
        agents = db.list_agents()
        scheduled_dict = scheduler.list_scheduled()
        scheduled = [{'id': k, **v} for k, v in scheduled_dict.items()]
        
        running_count = len([a for a in agents if a.get('status') == 'running'])
        completed_count = len([a for a in agents if a.get('status') == 'completed'])
        failed_count = len([a for a in agents if a.get('status') == 'failed'])
        
        return render_template('dashboard.html', 
                             agents=agents,
                             scheduled=scheduled,
                             stats={
                                 'running': running_count,
                                 'completed': completed_count,
                                 'failed': failed_count,
                                 'total': len(agents)
                             })

    @app.route('/agents')
    def agents():
        """Agents management page"""
        agents = db.list_agents()
        return render_template('agents.html', agents=agents)

    @app.route('/schedule')
    def schedule():
        """Schedule management page"""
        scheduled_dict = scheduler.list_scheduled()
        scheduled = [{'id': k, **v} for k, v in scheduled_dict.items()]
        return render_template('schedule.html', scheduled=scheduled)

    @app.route('/create-manifest')
    def create_manifest():
        """Create manifest page"""
        return render_template('create_manifest.html')

    @app.route('/run-agent', methods=['GET', 'POST'])
    def run_agent():
        """Run agent form"""
        if request.method == 'POST':
            manifest = request.form.get('manifest', 'default.yaml')
            task = request.form.get('task', '')
            
            if not task:
                return jsonify({'error': 'Task is required'}), 400
            
            try:
                from agentos.cli.cli_helpers import run_agent_background
                run_agent_background(manifest, task)
                return jsonify({'success': True, 'message': 'Agent started successfully'})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        manifests = []
        for yaml_file in Path('.').glob('*.yaml'):
            manifests.append(str(yaml_file))
        for yaml_file in Path('examples').glob('*.yaml'):
            manifests.append(str(yaml_file))
        
        return render_template('run_agent.html', manifests=manifests)

    @app.route('/api/agents')
    def api_agents():
        """API endpoint for agents data"""
        agents = db.list_agents()
        return jsonify(agents)

    @app.route('/api/schedule')
    def api_schedule():
        """API endpoint for schedule data"""
        scheduled_dict = scheduler.list_scheduled()
        scheduled = [{'id': k, **v} for k, v in scheduled_dict.items()]
        return jsonify(scheduled)

    @app.route('/api/agent/<agent_id>/logs')
    def api_agent_logs(agent_id):
        """API endpoint for agent logs"""
        agent = db.get_agent(agent_id)
        if not agent:
            return jsonify({'error': 'Agent not found'}), 404
        
        log_path = agent.get('log_path')
        if not log_path or not Path(log_path).exists():
            return jsonify({'logs': []})
        
        try:
            with open(log_path, 'r') as f:
                logs = f.readlines()[-50:]
            return jsonify({'logs': [line.strip() for line in logs]})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/agent/<agent_id>/stop', methods=['POST'])
    def api_stop_agent(agent_id):
        """API endpoint to stop an agent"""
        try:
            success = db.stop(agent_id)
            if success:
                return jsonify({'success': True, 'message': 'Agent stopped'})
            else:
                return jsonify({'error': 'Failed to stop agent'}), 500
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/schedule/<schedule_id>/remove', methods=['POST'])
    def api_remove_schedule(schedule_id):
        """API endpoint to remove scheduled agent"""
        try:
            db.remove_scheduled_agent(schedule_id)
            return jsonify({'success': True, 'message': 'Schedule removed'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/prune', methods=['POST'])
    def api_prune():
        """API endpoint to prune stopped agents"""
        try:
            db.prune()
            return jsonify({'success': True, 'message': 'Agents pruned'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/health')
    def health_check():
        """Health check endpoint for monitoring"""
        try:
            agents = db.list_agents()
            scheduler_status = 'running' if scheduler.running else 'stopped'
            
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'database': 'connected',
                'scheduler': scheduler_status,
                'agents_count': len(agents)
            }), 200
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }), 503

    @app.route('/metrics')
    def metrics():
        """Prometheus-style metrics endpoint"""
        try:
            agents = db.list_agents()
            running = len([a for a in agents if a.get('status') == 'running'])
            completed = len([a for a in agents if a.get('status') == 'completed'])
            failed = len([a for a in agents if a.get('status') == 'failed'])
            stopped = len([a for a in agents if a.get('status') == 'stopped'])
            
            metrics_text = f"""# HELP agentos_agents_total Total number of agents
# TYPE agentos_agents_total gauge
agentos_agents_total {len(agents)}

# HELP agentos_agents_running Number of running agents
# TYPE agentos_agents_running gauge
agentos_agents_running {running}

# HELP agentos_agents_completed Number of completed agents
# TYPE agentos_agents_completed gauge
agentos_agents_completed {completed}

# HELP agentos_agents_failed Number of failed agents
# TYPE agentos_agents_failed gauge
agentos_agents_failed {failed}

# HELP agentos_agents_stopped Number of stopped agents
# TYPE agentos_agents_stopped gauge
agentos_agents_stopped {stopped}

# HELP agentos_scheduler_status Scheduler status (1=running, 0=stopped)
# TYPE agentos_scheduler_status gauge
agentos_scheduler_status {1 if scheduler.running else 0}
"""
            return metrics_text, 200, {'Content-Type': 'text/plain; charset=utf-8'}
        except Exception as e:
            return f"# Error generating metrics: {e}", 500, {'Content-Type': 'text/plain; charset=utf-8'}

    @app.errorhandler(404)
    def not_found(e):
        """Handle 404 errors"""
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Endpoint not found'}), 404
        return render_template('dashboard.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        """Handle 500 errors"""
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error'}), 500
        return jsonify({'error': 'Internal server error'}), 500
