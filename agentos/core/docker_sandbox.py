"""Enhanced Docker Isolation for AgentOS"""

import logging
import os
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import docker
    from docker.errors import APIError, ContainerError, ImageNotFound, NotFound

    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    logger.warning("Docker module not available. Install with: pip install docker")


CONTAINER_NAME = "agentos-sandbox"
DEFAULT_IMAGE = "python:3.11-slim"


class DockerSandbox:
    """
    Docker-based sandboxed execution environment for AgentOS.
    Provides isolated command execution with resource limits.
    """

    _lock = threading.Lock()

    def __init__(
        self,
        image: str = DEFAULT_IMAGE,
        container_name: str = CONTAINER_NAME,
        memory_limit: str = "512m",
        cpu_quota: int = 50000,  # 50% of one CPU
        network_disabled: bool = False,
        auto_remove: bool = False,
        working_dir: str = "/workspace",
    ):
        """
        Initialize the Docker sandbox.

        Args:
            image: Docker image to use
            container_name: Name for the sandbox container
            memory_limit: Memory limit (e.g., '512m', '1g')
            cpu_quota: CPU quota in microseconds per 100ms period
            network_disabled: Disable network access in sandbox
            auto_remove: Auto-remove container when stopped
            working_dir: Working directory inside container
        """
        if not DOCKER_AVAILABLE:
            raise RuntimeError("Docker module not installed. Run: pip install docker")

        self.image = image
        self.container_name = container_name
        self.memory_limit = memory_limit
        self.cpu_quota = cpu_quota
        self.network_disabled = network_disabled
        self.auto_remove = auto_remove
        self.working_dir = working_dir

        self._client = None
        self._container = None

    @property
    def client(self):
        """Get Docker client, creating if needed."""
        if self._client is None:
            self._client = docker.from_env()
        return self._client

    def _ensure_image(self):
        """Ensure the Docker image is available."""
        try:
            self.client.images.get(self.image)
            logger.debug(f"Image {self.image} already available")
        except ImageNotFound:
            logger.info(f"Pulling image {self.image}...")
            self.client.images.pull(self.image)
            logger.info(f"Image {self.image} pulled successfully")

    def start(self) -> bool:
        """
        Start the sandbox container.

        Returns:
            True if container started, False otherwise
        """
        with self._lock:
            try:
                # Check for existing container
                try:
                    self._container = self.client.containers.get(self.container_name)
                    if self._container.status != "running":
                        logger.info(
                            f"Starting existing container '{self.container_name}'..."
                        )
                        self._container.start()
                    else:
                        logger.debug(
                            f"Container '{self.container_name}' already running"
                        )
                    return True
                except NotFound:
                    pass

                # Ensure image exists
                self._ensure_image()

                # Create new container
                logger.info(f"Creating sandbox container '{self.container_name}'...")
                self._container = self.client.containers.run(
                    self.image,
                    command="sleep infinity",
                    name=self.container_name,
                    detach=True,
                    tty=True,
                    mem_limit=self.memory_limit,
                    cpu_quota=self.cpu_quota,
                    network_disabled=self.network_disabled,
                    working_dir=self.working_dir,
                    restart_policy={"Name": "unless-stopped"},
                    auto_remove=self.auto_remove,
                    security_opt=["no-new-privileges"],  # Security hardening
                )
                logger.info(f"Sandbox container '{self.container_name}' created")
                return True

            except APIError as e:
                logger.error(f"Docker API error: {e}")
                return False
            except Exception as e:
                logger.error(f"Error starting sandbox: {e}")
                return False

    def stop(self, timeout: int = 10) -> bool:
        """
        Stop the sandbox container.

        Args:
            timeout: Timeout in seconds before force kill

        Returns:
            True if stopped, False otherwise
        """
        with self._lock:
            try:
                if self._container is None:
                    try:
                        self._container = self.client.containers.get(
                            self.container_name
                        )
                    except NotFound:
                        logger.debug("Container not found")
                        return True

                logger.info(f"Stopping sandbox container '{self.container_name}'...")
                self._container.stop(timeout=timeout)
                logger.info("Sandbox container stopped")
                return True

            except Exception as e:
                logger.error(f"Error stopping sandbox: {e}")
                return False

    def remove(self, force: bool = False) -> bool:
        """
        Remove the sandbox container.

        Args:
            force: Force remove even if running

        Returns:
            True if removed, False otherwise
        """
        with self._lock:
            try:
                if self._container is None:
                    try:
                        self._container = self.client.containers.get(
                            self.container_name
                        )
                    except NotFound:
                        return True

                logger.info(f"Removing sandbox container '{self.container_name}'...")
                self._container.remove(force=force)
                self._container = None
                logger.info("Sandbox container removed")
                return True

            except Exception as e:
                logger.error(f"Error removing sandbox: {e}")
                return False

    def execute(
        self,
        command: str,
        timeout: int = 60,
        user: str = "nobody",  # Run as non-root by default
        workdir: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> Tuple[int, str]:
        """
        Execute a command in the sandbox.

        Args:
            command: Command to execute
            timeout: Execution timeout in seconds
            user: User to run command as
            workdir: Working directory for command
            env: Environment variables

        Returns:
            Tuple of (exit_code, output)
        """
        if not command or not command.strip():
            return 1, "ERROR: Empty command"

        # Ensure container is running
        if not self.start():
            return 1, "ERROR: Failed to start sandbox container"

        try:
            logger.debug(f"Executing in sandbox: {command[:100]}...")

            # Execute command
            exec_result = self._container.exec_run(
                cmd=["sh", "-c", command],
                user=user,
                workdir=workdir or self.working_dir,
                environment=env,
                demux=True,  # Separate stdout/stderr
            )

            # Get output
            stdout = exec_result.output[0] or b""
            stderr = exec_result.output[1] or b""

            output = stdout.decode(errors="replace")
            if stderr:
                err_text = stderr.decode(errors="replace")
                if output:
                    output += f"\n[stderr]: {err_text}"
                else:
                    output = err_text

            return exec_result.exit_code, output.strip()

        except Exception as e:
            logger.error(f"Sandbox execution error: {e}")
            return 1, f"Sandbox error: {e}"

    def copy_to(self, local_path: str, container_path: str) -> bool:
        """
        Copy a file or directory to the sandbox.

        Args:
            local_path: Local file/directory path
            container_path: Destination path in container

        Returns:
            True if successful
        """
        import io
        import tarfile

        try:
            if not self.start():
                return False

            # Create tar archive
            tar_stream = io.BytesIO()
            with tarfile.open(fileobj=tar_stream, mode="w") as tar:
                tar.add(local_path, arcname=os.path.basename(local_path))
            tar_stream.seek(0)

            # Put to container
            self._container.put_archive(
                os.path.dirname(container_path) or "/", tar_stream.read()
            )

            logger.debug(f"Copied {local_path} to {container_path}")
            return True

        except Exception as e:
            logger.error(f"Error copying to sandbox: {e}")
            return False

    def copy_from(self, container_path: str, local_path: str) -> bool:
        """
        Copy a file or directory from the sandbox.

        Args:
            container_path: Path in container
            local_path: Local destination path

        Returns:
            True if successful
        """
        import io
        import tarfile

        try:
            if not self.start():
                return False

            # Get from container
            bits, stat = self._container.get_archive(container_path)

            # Extract tar archive
            tar_stream = io.BytesIO()
            for chunk in bits:
                tar_stream.write(chunk)
            tar_stream.seek(0)

            with tarfile.open(fileobj=tar_stream, mode="r") as tar:
                tar.extractall(os.path.dirname(local_path) or ".")

            logger.debug(f"Copied {container_path} to {local_path}")
            return True

        except Exception as e:
            logger.error(f"Error copying from sandbox: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """
        Get sandbox container status.

        Returns:
            Status dictionary
        """
        try:
            container = self.client.containers.get(self.container_name)
            return {
                "exists": True,
                "status": container.status,
                "id": container.short_id,
                "image": self.image,
                "memory_limit": self.memory_limit,
                "network_disabled": self.network_disabled,
            }
        except NotFound:
            return {
                "exists": False,
                "status": "not_created",
                "image": self.image,
            }
        except Exception as e:
            return {
                "exists": False,
                "status": "error",
                "error": str(e),
            }


# Global sandbox instance
_default_sandbox: Optional[DockerSandbox] = None


def get_sandbox() -> DockerSandbox:
    """Get the default sandbox instance."""
    global _default_sandbox
    if _default_sandbox is None:
        _default_sandbox = DockerSandbox()
    return _default_sandbox


def run_in_sandbox(
    command: str,
    timeout: int = 60,
    env: Optional[Dict[str, str]] = None,
) -> Tuple[int, str]:
    """
    Convenience function to run a command in the default sandbox.

    Args:
        command: Command to execute
        timeout: Execution timeout
        env: Environment variables

    Returns:
        Tuple of (exit_code, output)
    """
    return get_sandbox().execute(command, timeout=timeout, env=env)


def is_docker_available() -> bool:
    """Check if Docker is available."""
    if not DOCKER_AVAILABLE:
        return False
    try:
        client = docker.from_env()
        client.ping()
        return True
    except Exception:
        return False
