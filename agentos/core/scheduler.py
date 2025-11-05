#!/usr/bin/env python3
"""
AgentOS Scheduler - Handles time-based and recurring agent execution
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any
import logging
from agentos.database import db

logger = logging.getLogger(__name__)

class AgentScheduler:
    def __init__(self):
        self.scheduled_agents = {}
        self.running = False
        self.scheduler_thread = None
    
    def schedule_agent(self, agent_config: Dict[str, Any], task: str, manifest_path: str):
        """Schedule an agent based on time and repeat configuration"""
        agent_name = agent_config.get('name', 'unknown')
        time_config = agent_config.get('time')
        repeat_config = agent_config.get('repeat')
        
        if time_config is not None:
            # Schedule for specific time (24-hour format)
            schedule_id = f"{agent_name}_daily"
            next_run = self._get_next_daily_run(time_config)
            db.add_scheduled_agent(
                schedule_id, agent_name, manifest_path, task, 'daily',
                time_config=time_config, next_run=next_run.isoformat()
            )
            logger.info(f"Scheduled {agent_name} to run daily at {time_config:02d}:00")
        
        if repeat_config is not None:
            # Schedule for repeat interval (minutes)
            schedule_id = f"{agent_name}_repeat"
            next_run = datetime.now() + timedelta(minutes=repeat_config)
            db.add_scheduled_agent(
                schedule_id, agent_name, manifest_path, task, 'repeat',
                repeat_config=repeat_config, next_run=next_run.isoformat()
            )
            logger.info(f"Scheduled {agent_name} to repeat every {repeat_config} minutes")
    
    def _schedule_daily(self, name: str, hour: int, task: str, manifest_path: str, config: Dict):
        """Schedule agent to run daily at specific hour"""
        schedule_info = {
            'type': 'daily',
            'hour': hour,
            'task': task,
            'manifest_path': manifest_path,
            'config': config,
            'next_run': self._get_next_daily_run(hour)
        }
        self.scheduled_agents[f"{name}_daily"] = schedule_info
        logger.info(f"Scheduled {name} to run daily at {hour:02d}:00")
    
    def _schedule_repeat(self, name: str, minutes: int, task: str, manifest_path: str, config: Dict):
        """Schedule agent to run every N minutes"""
        schedule_info = {
            'type': 'repeat',
            'interval': minutes,
            'task': task,
            'manifest_path': manifest_path,
            'config': config,
            'next_run': datetime.now() + timedelta(minutes=minutes)
        }
        self.scheduled_agents[f"{name}_repeat"] = schedule_info
        logger.info(f"Scheduled {name} to repeat every {minutes} minutes")
    
    def _get_next_daily_run(self, hour: int) -> datetime:
        """Calculate next run time for daily schedule"""
        now = datetime.now()
        next_run = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        
        # If time has passed today, schedule for tomorrow
        if next_run <= now:
            next_run += timedelta(days=1)
        
        return next_run
    
    def start(self):
        """Start the scheduler daemon"""
        if self.running:
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        logger.info("AgentOS Scheduler started")
    
    def stop(self):
        """Stop the scheduler daemon"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join()
        logger.info("AgentOS Scheduler stopped")
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            now = datetime.now()
            
            # Load scheduled agents from database
            scheduled_agents = db.list_scheduled_agents()
            
            for agent in scheduled_agents:
                if agent['next_run']:
                    next_run = datetime.fromisoformat(agent['next_run'])
                    if now >= next_run:
                        self._execute_scheduled_agent_from_db(agent)
            
            time.sleep(30)  # Check every 30 seconds
    
    def _execute_scheduled_agent_from_db(self, agent: Dict):
        """Execute a scheduled agent from database record"""
        try:
            from agentos import run_agent_background
            
            logger.info(f"Executing scheduled agent: {agent['id']}")
            
            # Run agent in background
            run_agent_background(
                agent['manifest_path'],
                agent['task']
            )
            
            # Update next run time
            if agent['schedule_type'] == 'daily':
                next_run = self._get_next_daily_run(agent['time_config'])
            elif agent['schedule_type'] == 'repeat':
                next_run = datetime.now() + timedelta(minutes=agent['repeat_config'])
            else:
                return
                
            db.update_scheduled_next_run(agent['id'], next_run.isoformat())
            
        except Exception as e:
            logger.error(f"Failed to execute scheduled agent {agent['id']}: {e}")
    
    def list_scheduled(self) -> Dict:
        """List all scheduled agents from database"""
        result = {}
        scheduled_agents = db.list_scheduled_agents()
        
        for agent in scheduled_agents:
            schedule_id = agent['id']
            result[schedule_id] = {
                'type': agent['schedule_type'],
                'manifest': agent['manifest_path'],
                'task': agent['task'][:50] + '...' if len(agent['task']) > 50 else agent['task'],
                'time': agent.get('time_config'),
                'repeat': agent.get('repeat_config'),
                'next_run': agent['next_run'][:19] if agent['next_run'] else 'N/A'
            }
        return result

# Global scheduler instance
scheduler = AgentScheduler()