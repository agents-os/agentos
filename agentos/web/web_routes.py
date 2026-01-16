"""Web UI Routes for AgentOS"""

import json
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path

from flask import jsonify, render_template, request, session

from agentos.core import path_resolver
from agentos.core.scheduler import scheduler
from agentos.core.utils import MCP_ENABLED, MCP_SERVERS
from agentos.database import db
from agentos.llm.answerer import (
    get_claude_response,
    get_cohere_response,
    get_gemini_response,
    get_github_response,
    get_ollama_response,
    get_openai_response,
)
from agentos.mcp import MCPCall, MCPClient, MCPNotAvailable

# Provider mapping
CHAT_PROVIDERS = {
    "github": get_github_response,
    "gemini": get_gemini_response,
    "cohere": get_cohere_response,
    "openai": get_openai_response,
    "claude": get_claude_response,
    "ollama": get_ollama_response,
}

PROVIDER_MODELS = {
    "github": "openai/gpt-4o-mini",
    "gemini": "models/gemini-2.0-flash-lite",
    "cohere": "command-xlarge-nightly",
    "openai": "gpt-4o-mini",
    "claude": "claude-3-5-haiku-20241022",
    "ollama": "phi3",
}

# Agentic system prompt for web chat
AGENTIC_SYSTEM_PROMPT = """You are an AI assistant with the ability to execute shell commands on the user's system.

When the user asks you to perform a task that requires running commands (like creating files, deleting files, installing packages, etc.), provide the command in a bash code block like this:

```bash
command here
```

The system will automatically detect and execute these commands. After execution, you'll see the results.

Be helpful and when a task requires a command, always provide it in the proper format so it can be executed.
Keep your responses concise and action-oriented."""


# Agentic system prompt for MCP tool usage (web)
AGENTIC_MCP_SYSTEM_PROMPT = """You are an AI assistant with access to MCP (Model Context Protocol) tools.

AVAILABLE TOOLS:
- read_file(path, start_line?, end_line?) - Read file contents
- write_file(path, content, create_dirs?) - Write/create a file
- replace(path, old_string, new_string, count?) - Edit/replace text in a file
- list_directory(path?, recursive?, max_depth?) - List directory contents
- glob(pattern, root?) - Find files matching a pattern
- search_file_content(pattern, path?, is_regex?, include_pattern?, max_results?) - Search text in files
- run_shell_command(command, cwd?, timeout?, env?) - Execute a shell command
- web_fetch(url, method?, headers?, body?, timeout?) - Fetch URL content
- google_web_search(query, num_results?) - Web search
- save_memory(key, value) / get_memory(key) - Store/retrieve values
- write_todos(todos) / read_todos() - Manage todo list
- delegate_to_agent(task, agent_name?, context?) - Delegate to another agent

Respond with a JSON code block:
```json
{
  "mcp_calls": [
    {"server": "builtin", "tool": "<tool_name>", "args": {"arg1": "value1"}}
  ]
}
```

Use "builtin" as server. Prefer MCP tools over shell commands.
"""


def run_shell_command(command: str, timeout: int = 60):
    """Execute a shell command and return the result."""
    if not command or not command.strip():
        return {"success": False, "output": "Empty command"}

    command = command.strip()

    # Block dangerous commands
    dangerous = ["rm -rf /", "rm -rf ~", "mkfs", "dd if=", ":(){", "fork bomb"]
    if any(d in command.lower() for d in dangerous):
        return {"success": False, "output": "Dangerous command blocked"}

    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
            text=True,
            cwd=os.getcwd(),
            env=os.environ.copy(),
        )

        try:
            output, _ = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            return {"success": False, "output": "Command timed out"}

        return {
            "success": process.returncode == 0,
            "output": output.strip() if output else "(no output)",
            "returncode": process.returncode,
        }
    except Exception as e:
        return {"success": False, "output": str(e)}


def extract_commands(response: str):
    """Extract bash commands from response."""
    pattern = r"```(?:bash|sh|shell)?\s*\n(.*?)```"
    matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
    commands = []
    for match in matches:
        for line in match.strip().split("\n"):
            line = line.strip()
            if line and not line.startswith("#"):
                commands.append(line)
    return commands


def extract_mcp_calls(response: str):
    pattern = r"```json\s*\n(.*?)```"
    matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
    for m in matches:
        try:
            obj = json.loads(m)
            calls = obj.get("mcp_calls") or obj.get("tools") or []
            out = []
            for c in calls:
                server = str(c.get("server") or "").strip()
                tool = str(c.get("tool") or "").strip()
                args = c.get("args") or {}
                if server and tool and isinstance(args, dict):
                    out.append(MCPCall(server=server, tool=tool, args=args))
            if out:
                return out
        except Exception:
            continue
    return []


def register_routes(app):
    """Register all routes with the Flask app"""

    @app.route("/")
    def dashboard():
        """Main dashboard showing agents and schedules"""
        agents = db.list_agents()
        scheduled_dict = scheduler.list_scheduled()
        scheduled = [{"id": k, **v} for k, v in scheduled_dict.items()]

        running_count = len([a for a in agents if a.get("status") == "running"])
        completed_count = len([a for a in agents if a.get("status") == "completed"])
        failed_count = len([a for a in agents if a.get("status") == "failed"])

        return render_template(
            "dashboard.html",
            agents=agents,
            scheduled=scheduled,
            stats={
                "running": running_count,
                "completed": completed_count,
                "failed": failed_count,
                "total": len(agents),
            },
        )

    @app.route("/agents")
    def agents():
        """Agents management page"""
        agents = db.list_agents()
        return render_template("agents.html", agents=agents)

    @app.route("/schedule")
    def schedule():
        """Schedule management page"""
        scheduled_dict = scheduler.list_scheduled()
        scheduled = [{"id": k, **v} for k, v in scheduled_dict.items()]
        return render_template("schedule.html", scheduled=scheduled)

    @app.route("/create-manifest")
    def create_manifest():
        """Create manifest page"""
        return render_template("create_manifest.html")

    @app.route("/run-agent", methods=["GET", "POST"])
    def run_agent():
        """Run agent form"""
        if request.method == "POST":
            manifest = request.form.get("manifest", "default.yaml")
            task = request.form.get("task", "")

            if not task:
                return jsonify({"error": "Task is required"}), 400

            try:
                from agentos.cli.cli_helpers import run_agent_background

                run_agent_background(manifest, task)
                return jsonify(
                    {"success": True, "message": "Agent started successfully"}
                )
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        # Discover manifests from multiple locations
        manifests = []
        manifest_dirs = [
            Path.cwd(),  # Current working directory
            Path.home(),  # Home directory
            Path(__file__).parent.parent.parent,  # Project root
        ]

        for manifest_dir in manifest_dirs:
            if manifest_dir.exists():
                for yaml_file in manifest_dir.glob("*.yaml"):
                    manifest_str = str(yaml_file)
                    if manifest_str not in manifests:
                        manifests.append(manifest_str)

        # Also check examples directory
        examples_dir = Path(__file__).parent.parent.parent / "examples"
        if examples_dir.exists():
            for yaml_file in examples_dir.glob("*.yaml"):
                manifest_str = str(yaml_file)
                if manifest_str not in manifests:
                    manifests.append(manifest_str)

        return render_template("run_agent.html", manifests=manifests)

    @app.route("/chat")
    def chat():
        """Chat interface page"""
        # Initialize session for chat history if not exists
        if "chat_history" not in session:
            session["chat_history"] = []

        return render_template(
            "chat.html",
            providers=["github", "gemini", "cohere", "openai", "claude", "ollama"],
        )

    @app.route("/api/chat", methods=["POST"])
    def api_chat():
        """API endpoint for chat"""
        try:
            data = request.get_json()
            message = data.get("message", "").strip()
            provider = data.get("provider", "github")
            model = data.get("model", "")
            temperature = float(data.get("temperature", 0.7))

            if not message:
                return jsonify({"error": "Message is required"}), 400

            # Get the appropriate response function
            response_func = CHAT_PROVIDERS.get(provider)
            if not response_func:
                return jsonify({"error": f"Provider {provider} not supported"}), 400

            # Use default model if not specified
            if not model:
                model = PROVIDER_MODELS.get(provider, "")

            # Get response from LLM with agentic system prompt
            response = response_func(
                query=message,
                system_prompt=AGENTIC_MCP_SYSTEM_PROMPT
                if MCP_ENABLED
                else AGENTIC_SYSTEM_PROMPT,
                model=model,
                temperature=temperature,
            )

            # Extract MCP calls or commands
            mcp_calls = extract_mcp_calls(response) if MCP_ENABLED else []
            commands = [] if mcp_calls else extract_commands(response)

            mcp_results = []
            mcp_error = None
            if MCP_ENABLED and mcp_calls:
                try:
                    client = MCPClient(servers=MCP_SERVERS)
                    client.connect()
                    for call in mcp_calls:
                        try:
                            res = client.call(call)
                        except Exception as e:
                            res = {"success": False, "error": str(e)}
                        mcp_results.append(
                            {
                                "server": call.server,
                                "tool": call.tool,
                                "result": res,
                            }
                        )
                except MCPNotAvailable as e:
                    mcp_error = str(e)

            # Store in session history
            if "chat_history" not in session:
                session["chat_history"] = []

            session["chat_history"].append(
                {
                    "role": "user",
                    "content": message,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
            session["chat_history"].append(
                {
                    "role": "assistant",
                    "content": response,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

            # Keep only last 50 messages
            session["chat_history"] = session["chat_history"][-50:]
            session.modified = True

            return jsonify(
                {
                    "success": True,
                    "response": response,
                    "provider": provider,
                    "commands": commands,
                    "mcp_calls": [
                        {"server": c.server, "tool": c.tool, "args": c.args}
                        for c in mcp_calls
                    ],
                    "mcp_results": mcp_results,
                    "mcp_error": mcp_error,
                }
            )
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/chat/execute", methods=["POST"])
    def api_chat_execute():
        """API endpoint to execute a command"""
        try:
            data = request.get_json()
            command = data.get("command", "").strip()

            if not command:
                return jsonify({"error": "Command is required"}), 400

            result = run_shell_command(command)

            return jsonify(
                {
                    "success": result["success"],
                    "output": result["output"],
                    "command": command,
                }
            )
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/chat/execute-mcp", methods=["POST"])
    def api_chat_execute_mcp():
        """API endpoint to execute MCP tool calls"""
        try:
            data = request.get_json()
            mcp_calls_data = data.get("mcp_calls", [])

            if not mcp_calls_data:
                return jsonify({"error": "No MCP calls provided"}), 400

            # Convert to MCPCall objects
            calls = []
            for c in mcp_calls_data:
                server = str(c.get("server") or "builtin").strip()
                tool = str(c.get("tool") or "").strip()
                args = c.get("args") or {}
                if tool and isinstance(args, dict):
                    calls.append(MCPCall(server=server, tool=tool, args=args))

            if not calls:
                return jsonify({"error": "No valid MCP calls"}), 400

            # Execute all calls
            results = []
            client = MCPClient(servers=MCP_SERVERS)

            for call in calls:
                try:
                    res = client.call(call)
                except Exception as e:
                    res = {"success": False, "error": str(e)}

                results.append(
                    {
                        "server": call.server,
                        "tool": call.tool,
                        "args": call.args,
                        "result": res,
                    }
                )

            return jsonify(
                {
                    "success": True,
                    "results": results,
                }
            )
        except MCPNotAvailable as e:
            return jsonify({"error": f"MCP not available: {e}"}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/chat/summarize", methods=["POST"])
    def api_chat_summarize():
        """API endpoint to get a follow-up answer after MCP execution"""
        try:
            data = request.get_json()
            original_question = data.get("question", "").strip()
            mcp_results = data.get("results", [])
            provider = data.get("provider", "github")
            model = data.get("model", "")
            temperature = float(data.get("temperature", 0.7))

            if not original_question or not mcp_results:
                return jsonify({"error": "Question and results required"}), 400

            # Get response function
            response_func = CHAT_PROVIDERS.get(provider)
            if not response_func:
                return jsonify({"error": f"Provider {provider} not supported"}), 400

            if not model:
                model = PROVIDER_MODELS.get(provider, "")

            # Build context from results
            results_context = []
            for r in mcp_results:
                if r.get("result", {}).get("success"):
                    output = r["result"].get("output", "")
                    tool = r.get("tool", "unknown")
                    if isinstance(output, list):
                        # Format search results
                        formatted = "\n".join(
                            f"- {item.get('title', '')}: {item.get('snippet', '')[:200]} ({item.get('url', '')})"
                            for item in output[:5]
                        )
                        results_context.append(f"[{tool} results]:\n{formatted}")
                    else:
                        results_context.append(
                            f"[{tool} output]:\n{str(output)[:1000]}"
                        )

            if not results_context:
                return jsonify({"error": "No successful results to summarize"}), 400

            # Generate follow-up response
            followup_prompt = f"""Based on the tool results below, provide a helpful answer to the user's original question.

Tool Results:
{chr(10).join(results_context)}

Original question: {original_question}

Provide a clear, concise answer based on the information above. Do NOT output any JSON or mcp_calls - just answer naturally."""

            followup_response = response_func(
                query=followup_prompt,
                system_prompt="You are a helpful assistant. Answer the user's question based on the provided tool results. Be concise and informative.",
                model=model,
                temperature=temperature,
            )

            return jsonify(
                {
                    "success": True,
                    "answer": followup_response,
                }
            )
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/chat/clear", methods=["POST"])
    def api_chat_clear():
        """API endpoint to clear chat history"""
        session["chat_history"] = []
        session.modified = True
        return jsonify({"success": True, "message": "Chat history cleared"})

    @app.route("/api/chat/history")
    def api_chat_history():
        """API endpoint to get chat history"""
        history = session.get("chat_history", [])
        return jsonify({"history": history})

    @app.route("/api/agents")
    def api_agents():
        """API endpoint for agents data"""
        agents = db.list_agents()
        return jsonify(agents)

    @app.route("/api/schedule")
    def api_schedule():
        """API endpoint for schedule data"""
        scheduled_dict = scheduler.list_scheduled()
        scheduled = [{"id": k, **v} for k, v in scheduled_dict.items()]
        return jsonify(scheduled)

    @app.route("/api/agent/<agent_id>/logs")
    def api_agent_logs(agent_id):
        """API endpoint for agent logs"""
        agent = db.get_agent(agent_id)
        if not agent:
            return jsonify({"error": "Agent not found"}), 404

        log_path = agent.get("log_path")
        if not log_path or not Path(log_path).exists():
            return jsonify({"logs": []})

        try:
            with open(log_path, "r") as f:
                logs = f.readlines()[-50:]
            return jsonify({"logs": [line.strip() for line in logs]})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/agent/<agent_id>/stop", methods=["POST"])
    def api_stop_agent(agent_id):
        """API endpoint to stop an agent"""
        try:
            success = db.stop(agent_id)
            if success:
                return jsonify({"success": True, "message": "Agent stopped"})
            else:
                return jsonify({"error": "Failed to stop agent"}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/schedule/<schedule_id>/remove", methods=["POST"])
    def api_remove_schedule(schedule_id):
        """API endpoint to remove scheduled agent"""
        try:
            db.remove_scheduled_agent(schedule_id)
            return jsonify({"success": True, "message": "Schedule removed"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/prune", methods=["POST"])
    def api_prune():
        """API endpoint to prune stopped agents"""
        try:
            db.prune()
            return jsonify({"success": True, "message": "Agents pruned"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/health")
    def health_check():
        """Health check endpoint for monitoring"""
        try:
            agents = db.list_agents()
            scheduler_status = "running" if scheduler.running else "stopped"

            return jsonify(
                {
                    "status": "healthy",
                    "timestamp": datetime.utcnow().isoformat(),
                    "database": "connected",
                    "scheduler": scheduler_status,
                    "agents_count": len(agents),
                }
            ), 200
        except Exception as e:
            return jsonify(
                {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ), 503

    @app.route("/metrics")
    def metrics():
        """Prometheus-style metrics endpoint"""
        try:
            agents = db.list_agents()
            running = len([a for a in agents if a.get("status") == "running"])
            completed = len([a for a in agents if a.get("status") == "completed"])
            failed = len([a for a in agents if a.get("status") == "failed"])
            stopped = len([a for a in agents if a.get("status") == "stopped"])

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
            return metrics_text, 200, {"Content-Type": "text/plain; charset=utf-8"}
        except Exception as e:
            return (
                f"# Error generating metrics: {e}",
                500,
                {"Content-Type": "text/plain; charset=utf-8"},
            )

    @app.errorhandler(404)
    def not_found(e):
        """Handle 404 errors"""
        if request.path.startswith("/api/"):
            return jsonify({"error": "Endpoint not found"}), 404
        return render_template("dashboard.html"), 404

    @app.errorhandler(500)
    def internal_error(e):
        """Handle 500 errors"""
        if request.path.startswith("/api/"):
            return jsonify({"error": "Internal server error"}), 500
        return jsonify({"error": "Internal server error"}), 500
