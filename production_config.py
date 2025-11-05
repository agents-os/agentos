"""
Production Configuration for AgentOS
Validates environment and provides secure defaults
"""

import os
import sys
from pathlib import Path

class ProductionConfig:
    """Production configuration with validation"""
    
    # Required environment variables
    REQUIRED_ENV_VARS = []
    
    # Optional with defaults
    OPTIONAL_ENV_VARS = {
        'AGENTOS_SECRET_KEY': 'change-this-in-production',
        'AGENTOS_LOG_LEVEL': 'INFO',
        'AGENTOS_MAX_AGENTS': '100',
        'AGENTOS_COMMAND_TIMEOUT': '30',
        'AGENTOS_MAX_STEPS': '10',
        'FLASK_ENV': 'production',
    }
    
    # API Keys (at least one required)
    API_KEY_VARS = [
        'GIT_HUB_TOKEN',
        'OPENAI_API_KEY',
        'CLAUDE_API_KEY',
        'GEMINI_API_KEY',
        'COHERE_API_KEY',
    ]
    
    @classmethod
    def validate(cls):
        """Validate production configuration"""
        errors = []
        warnings = []
        
        # Check required vars
        for var in cls.REQUIRED_ENV_VARS:
            if not os.environ.get(var):
                errors.append(f"Missing required environment variable: {var}")
        
        # Check API keys
        has_api_key = any(os.environ.get(var) for var in cls.API_KEY_VARS)
        if not has_api_key:
            warnings.append(f"No API keys found. Set at least one of: {', '.join(cls.API_KEY_VARS)}")
        
        # Check secret key
        secret_key = os.environ.get('AGENTOS_SECRET_KEY', cls.OPTIONAL_ENV_VARS['AGENTOS_SECRET_KEY'])
        if secret_key == 'change-this-in-production':
            warnings.append("AGENTOS_SECRET_KEY is using default value. Set a secure random key in production.")
        
        # Set defaults for optional vars
        for var, default in cls.OPTIONAL_ENV_VARS.items():
            if not os.environ.get(var):
                os.environ[var] = default
        
        return errors, warnings
    
    @classmethod
    def get_config(cls):
        """Get current configuration as dict"""
        return {
            'log_level': os.environ.get('AGENTOS_LOG_LEVEL', 'INFO'),
            'max_agents': int(os.environ.get('AGENTOS_MAX_AGENTS', '100')),
            'command_timeout': int(os.environ.get('AGENTOS_COMMAND_TIMEOUT', '30')),
            'max_steps': int(os.environ.get('AGENTOS_MAX_STEPS', '10')),
            'flask_env': os.environ.get('FLASK_ENV', 'production'),
            'secret_key': os.environ.get('AGENTOS_SECRET_KEY'),
        }
    
    @classmethod
    def print_config(cls):
        """Print configuration (without secrets)"""
        config = cls.get_config()
        print("=" * 50)
        print("AgentOS Production Configuration")
        print("=" * 50)
        for key, value in config.items():
            if 'key' in key.lower() or 'secret' in key.lower():
                print(f"{key}: {'*' * 8}")
            else:
                print(f"{key}: {value}")
        print("=" * 50)


def validate_production_env():
    """Validate production environment and print warnings"""
    errors, warnings = ProductionConfig.validate()
    
    if errors:
        print("❌ PRODUCTION CONFIGURATION ERRORS:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)
    
    if warnings:
        print("⚠️  PRODUCTION CONFIGURATION WARNINGS:")
        for warning in warnings:
            print(f"  - {warning}")
        print()
    
    return True


if __name__ == '__main__':
    validate_production_env()
    ProductionConfig.print_config()
