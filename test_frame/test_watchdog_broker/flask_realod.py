# -*- coding: utf-8 -*-
"""
Automatic Flask reloading using watchdog

Advantages:
1. Does not depend on Flask's built-in debug reloader; more stable
2. Only monitors the specified directory; avoids unrelated file changes triggering a restart
3. Even if the code has a syntax error, the monitoring process will not crash
4. Configurable restart delay to prevent restarting mid-save
"""

import subprocess
import sys
import time
import os
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler


class FlaskReloader:
    """Flask automatic reloader"""

    def __init__(self, flask_script: str, watch_dirs: list = None,
                 watch_files: list = None, patterns: list = None, delay: float = 1.0):
        """
        Args:
            flask_script: Path to the Flask startup script
            watch_dirs: List of directories to monitor (all files under each directory)
            watch_files: List of individual files to monitor (exact match)
            patterns: File patterns to monitor; default is ['*.py']
            delay: Number of seconds to wait after detecting a change before restarting; default is 1 second
        """
        self.flask_script = flask_script
        self.watch_dirs = [Path(d) for d in (watch_dirs or [])]
        # List of individual files, stored as normalized absolute paths
        self.watch_files = [Path(f).resolve() for f in (watch_files or [])]
        self.patterns = patterns or ['*.py']
        self.delay = delay
        self.process = None
        self.observer = None
        self._last_change_time = 0
        self._pending_restart = False

    def start_flask(self):
        """Start the Flask process"""
        if self.process:
            self.stop_flask()

        print(f"\n{'='*60}")
        print(f"[FlaskReloader] Starting Flask: {self.flask_script}")
        print(f"{'='*60}\n")

        # Start Flask using the current Python interpreter
        self.process = subprocess.Popen(
            [sys.executable, self.flask_script],
            cwd=os.path.dirname(self.flask_script) or '.',
        )

    def stop_flask(self):
        """Stop the Flask process"""
        if self.process:
            print(f"\n[FlaskReloader] Stopping Flask (PID: {self.process.pid})")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None

    def restart_flask(self):
        """Restart Flask"""
        print(f"\n[FlaskReloader] File change detected; restarting in {self.delay} seconds...")
        time.sleep(self.delay)
        self.start_flask()
        self._pending_restart = False

    def on_file_changed(self, event):
        """File change callback"""
        # Ignore directory events
        if event.is_directory:
            return

        src_path = Path(event.src_path).resolve()

        # If a list of individual files is specified, check if the file is in the list
        if self.watch_files:
            # Check for exact match with an individual file
            if src_path not in self.watch_files:
                # Not in the individual file list; check if it is under a monitored directory
                in_watch_dir = False
                for d in self.watch_dirs:
                    try:
                        src_path.relative_to(d.resolve())
                        in_watch_dir = True
                        break
                    except ValueError:
                        continue
                if not in_watch_dir:
                    return  # Not within the monitored scope; ignore

        # Debounce: multiple changes in a short time trigger only one restart
        now = time.time()
        if now - self._last_change_time < 0.5:
            return
        self._last_change_time = now

        print(f"[FlaskReloader] File changed: {src_path}")

        # Mark for restart; handled in the main loop
        self._pending_restart = True

    def run(self):
        """Run the reloader"""
        # Create the event handler
        handler = PatternMatchingEventHandler(
            patterns=self.patterns,
            ignore_patterns=['*/__pycache__/*', '*.pyc'],
            ignore_directories=True,
            case_sensitive=False,
        )
        handler.on_modified = self.on_file_changed
        handler.on_created = self.on_file_changed

        # Create the observer and add monitored directories
        self.observer = Observer()

        # Collect all directories to monitor (including parent directories of individual files)
        all_watch_dirs = set(self.watch_dirs)
        for f in self.watch_files:
            all_watch_dirs.add(f.parent)

        for watch_dir in all_watch_dirs:
            if watch_dir.exists():
                self.observer.schedule(handler, str(watch_dir), recursive=True)
                print(f"[FlaskReloader] Monitoring directory: {watch_dir}")
            else:
                print(f"[FlaskReloader] Warning: directory does not exist {watch_dir}")

        # Start the observer and Flask
        self.observer.start()
        self.start_flask()

        print("\n[FlaskReloader] Auto-reload started; press Ctrl+C to stop\n")

        try:
            while True:
                # Check if a restart is needed
                if self._pending_restart:
                    self.restart_flask()

                # Check if the Flask process has exited unexpectedly
                if self.process and self.process.poll() is not None:
                    print(f"\n[FlaskReloader] Flask process exited (code: {self.process.returncode})")
                    print("[FlaskReloader] Waiting for file change to trigger automatic restart...")
                    self.process = None
                    # Wait for the next file change to trigger a restart

                time.sleep(0.5)

        except KeyboardInterrupt:
            print("\n[FlaskReloader] Interrupt signal received; stopping...")
        finally:
            self.stop_flask()
            self.observer.stop()
            self.observer.join()
            print("[FlaskReloader] Stopped")


if __name__ == '__main__':
    # Project root directory
    PROJECT_ROOT = Path(__file__).parent.parent.parent

    # Flask startup script
    FLASK_SCRIPT = str(PROJECT_ROOT / 'funboost' / 'funweb' / 'app_debug_start.py')

    # Directories to monitor (any .py file change under these directories triggers a restart)
    WATCH_DIRS = [
        PROJECT_ROOT / 'funboost' / 'faas',
        PROJECT_ROOT / 'funboost' / 'funweb',
    ]

    # Individual files to monitor (exact match; only changes to these files trigger a restart)
    WATCH_FILES = [
        PROJECT_ROOT / 'funboost' / 'core' / 'active_cousumer_info_getter.py',
    ]

    # Individual files require monitoring their parent directory, but only filtered in the callback
    watch_dirs_for_observer = list(WATCH_DIRS)
    for f in WATCH_FILES:
        if f.parent not in watch_dirs_for_observer:
            watch_dirs_for_observer.append(f.parent)

    print("=" * 60)
    print("Flask watchdog auto-reloader")
    print("=" * 60)
    print(f"Flask script: {FLASK_SCRIPT}")
    print("Monitored directories:")
    for d in WATCH_DIRS:
        print(f"  - {d}")
    print("Monitored individual files:")
    for f in WATCH_FILES:
        print(f"  - {f}")
    print("=" * 60)

    reloader = FlaskReloader(
        flask_script=FLASK_SCRIPT,
        watch_dirs=WATCH_DIRS,
        watch_files=WATCH_FILES,
        patterns=['*.py'],
        delay=5.0,  # Wait 5 seconds after detecting a change before restarting.
    )
    reloader.run()
