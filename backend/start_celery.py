import subprocess
import sys
import os
import signal
import time
import platform


CELERY_APP = "app.workers.tasks.celery_app"


def main():
    backend_dir = os.path.dirname(os.path.abspath(__file__))

    worker_args = [
        sys.executable, "-m", "celery",
        "-A", CELERY_APP,
        "worker", "--loglevel=info",
    ]
    if platform.system() == "Windows":
        worker_args.extend(["-P", "solo"])

    worker = subprocess.Popen(worker_args, cwd=backend_dir)
    beat = subprocess.Popen(
        [sys.executable, "-m", "celery",
         "-A", CELERY_APP,
         "beat", "--loglevel=info"],
        cwd=backend_dir,
    )

    def shutdown(sig, frame):
        worker.terminate()
        beat.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        while True:
            if worker.poll() is not None:
                print(f"Worker exited with code {worker.returncode}")
                beat.terminate()
                sys.exit(1)
            if beat.poll() is not None:
                print(f"Beat exited with code {beat.returncode}")
                worker.terminate()
                sys.exit(1)
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown(None, None)


if __name__ == "__main__":
    main()
