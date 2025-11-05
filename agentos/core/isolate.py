import os

import docker

client = docker.from_env()
CONTAINER_NAME = "AgentOs"


def get_or_create_container(image="ubuntu:latest"):
    """
    Ensure the container named 'AgentOs' exists and is running.
    Returns the container object.
    """
    try:
        container = client.containers.get(CONTAINER_NAME)
        if container.status != "running":
            print(f"Starting existing container '{CONTAINER_NAME}'...")
            container.start()
        else:
            print(f"Reusing running container '{CONTAINER_NAME}'.")
    except docker.errors.NotFound:
        print(f"Creating new container '{CONTAINER_NAME}' from {image}...")
        container = client.containers.run(
            image,
            command="sleep infinity",  # Keep it alive
            name=CONTAINER_NAME,
            detach=True,
            tty=True,
            restart_policy={"Name": "always"},  # Auto-start on reboot
        )
    return container


def run_in_agentos(command):
    """
    Run a shell command inside the persistent 'AgentOs' container.
    Returns the command output.
    """
    container = get_or_create_container()
    exec_result = container.exec_run(command)
    output = exec_result.output.decode(errors="ignore").strip()
    return output


def remove_agentos():
    """
    Stop and remove the 'AgentOs' container permanently.
    """
    try:
        container = client.containers.get(CONTAINER_NAME)
        print("Stopping and removing AgentOs container...")
        container.stop()
        container.remove()
        print("AgentOs container removed successfully.")
    except docker.errors.NotFound:
        print("No AgentOs container found to remove.")


if __name__ == "__main__":
    # Example usage
    # print(run_in_agentos("echo 'Hello from AgentOs container!'"))
    # print(run_in_agentos("ls"))
    # print(run_in_agentos("uname -a"))
    # remove_agentos()
    # Uncomment to remove the persistent container
    # remove_agentos()
    while True:
        cmd = input(">>> ")
        if cmd == "clear":
            os.system("clear")
        elif cmd == "exit":
            break
        elif cmd == "remove":
            remove_agentos()
            break
        print(run_in_agentos(cmd))
