import multiprocessing
import os
import time


def run_in_separate_process(func, *args, **kwargs):
    """
    Runs a given function in a separate process, streams its logs,
    and returns (pid, process, queue).
    """

    def target(queue, *args, **kwargs):
        """Target function that pushes log messages into the queue."""
        pid = os.getpid()
        queue.put(f"[PID {pid}] Started")
        try:
            func(queue, *args, **kwargs)
        except Exception as e:
            queue.put(f"[PID {pid}] Error: {e}")
        finally:
            queue.put(f"[PID {pid}] Exiting")

    # Create a message queue for logs
    queue = multiprocessing.Queue()

    # Spawn a new process
    process = multiprocessing.Process(target=target, args=(queue, *args), kwargs=kwargs)
    process.start()

    return process.pid, process, queue


# --- Example function that logs messages ---
def test_function(queue):
    for i in range(5):
        queue.put(f"[PID {os.getpid()}] Iteration {i}")
        time.sleep(1)
    queue.put(f"[PID {os.getpid()}] Done!")


# --- Example usage ---
if __name__ == "__main__":
    pid, proc, q = run_in_separate_process(test_function)

    print(f"Main PID={os.getpid()} | Child PID={pid}\n")

    # Stream logs from the child process
    while proc.is_alive() or not q.empty():
        try:
            msg = q.get(timeout=0.5)
            print(msg)
        except:
            pass  # No message yet, keep looping

    proc.join()
    print(f"Process {pid} finished.")
