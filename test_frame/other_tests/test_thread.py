import threading
import time

def worker():  # Non-daemon thread
    while True:
        print("Worker running...")
        time.sleep(1)

def daemon_worker():  # Daemon thread
    while True:
        print("Daemon running...")
        time.sleep(1)

if __name__ == '__main__':
    # Start non-daemon thread (default daemon=False)
    t1 = threading.Thread(target=worker)
    t1.start()

    # Start daemon thread
    t2 = threading.Thread(target=daemon_worker, daemon=True)
    t2.start()

    print("Main thread ended")