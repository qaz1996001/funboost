# -*- coding: utf-8 -*-

"""
# Part 1: How to use
This file demonstrates how to implement an event-driven broker using register_custom_broker.

Watchdog File System Monitoring Broker - Event-Driven Message Queue

Design philosophy:
    - No need to publish messages manually; file system events automatically become messages
    - Similar to MYSQL_CDC, this is an event-driven broker
    - Suitable for: file processing pipelines, log monitoring, hot reloading, file synchronization,
      file-change-event-driven consumption

Usage: (Tutorial chapter 11.10 has a specific complete example)


    @boost(BoosterParams(
        queue_name='file_processor',
        broker_kind=BrokerEnum.WATCHDOG,
        broker_exclusive_config={
            'watch_path': './data/inbox',
            'patterns': ['*.csv', '*.json'],
            'event_types': ['created'],
            'ack_action': 'delete',
        }
    ))
    def process_file(event_type, src_path, dest_path, is_directory, timestamp, file_content,):  # Function parameters are fixed to these
        print(f"File received: {src_path}")
        return f"Processing complete"

    if __name__ == '__main__':
        process_file.consume()  # Simply place files in ./data/inbox to trigger automatic consumption



# Part 2: Why it is better than native watchdog
The watchdog broker implemented by funboost is more powerful than using native watchdog directly,
because funboost implements features that native watchdog does not support:

1. Comes with 30+ funboost concurrency control features, such as concurrency, qps, retry, etc.
2. funboost supports 'existing' in event_types, which native watchdog does not.
   This perfectly handles files that accumulated while the funboost service was stopped,
   or processes historically existing files that cannot be triggered in native watchdog.
3. Simpler code: native watchdog requires inheriting EventHandler and writing an Observer;
   funboost only needs a single consuming function to automatically handle all file events.
4. Built-in debounce: multiple operations on the same file within a short time only trigger one consumption.


# Part 3: Creative alternative use:
You can treat a folder as a message queue, where each file taskidxx.json in the folder is one message.
This is essentially using the disk as a message queue.

"""

import os
import shutil
import threading
import time
from fnmatch import fnmatch
from pathlib import Path
from typing import Optional, List

try:
    from watchdog.observers import Observer
    from watchdog.events import PatternMatchingEventHandler
except ImportError:
    raise ImportError("Please install watchdog: pip install watchdog")

from funboost import register_custom_broker, AbstractConsumer, AbstractPublisher, register_broker_exclusive_config_default
from funboost.core.helper_funs import get_task_id



# ============================================================================
# Publisher Implementation
# ============================================================================

class WatchdogPublisher(AbstractPublisher):
    """
    Watchdog Publisher

    Publishing a message = creating a file in the monitored directory.
    This triggers the watchdog 'created' event, which is then captured by the consumer.
    """

    def custom_init(self):
        super().custom_init()
        watch_path = self.publisher_params.broker_exclusive_config['watch_path']
        self._queue_dir = Path(watch_path)
        self._queue_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Watchdog Publisher initialized, monitored directory: {self._queue_dir.absolute().as_posix()}")

    def _publish_impl(self, msg: str):
        """
        When watchdog is used as a broker, manual message publishing is not required, but it is still supported.
        Publishing a message means funboost writes a file; after watchdog detects the file change,
        it automatically triggers the consuming function.
        """
        # raise NotImplementedError("Watchdog Broker is event-driven and does not support manual push. Please operate files directly in the monitored directory.")
        task_id = get_task_id(msg)
        file = self._queue_dir.joinpath(f'{task_id}.json')
        # Publishing means writing the message to a file, which automatically triggers the consuming function.
        file.write_text(msg)

    def clear(self):
        """Clear all message files in the monitored directory"""
        # Note: this may delete all files in the monitored directory — use with caution
        pass

    def get_message_count(self) -> int:
        """Count the number of files pending processing"""
        if not self._queue_dir.exists():
            return 0
        # Simple file count, non-recursive
        return len([f for f in self._queue_dir.iterdir() if f.is_file()])

    def close(self):
        pass


# ============================================================================
# Consumer Implementation
# ============================================================================

class FunboostEventHandler(PatternMatchingEventHandler):
    """
    Funboost-specific file event handler

    When a file event occurs, wraps the event info as a message and submits it to the consumer for processing
    """

    def __init__(self, consumer: 'WatchdogConsumer', event_types: List[str],
                 read_file_content: bool = False, debounce_seconds: Optional[float] = None, **kwargs):
        super().__init__(**kwargs)
        self._consumer = consumer
        self._event_types = set(event_types)
        self._read_file_content = read_file_content
        self._debounce_seconds = debounce_seconds
        # Debounce-related: store Timer and latest event info for each file path
        self._debounce_timers = {}  # {file_path: Timer}
        self._debounce_lock = threading.Lock()

    def _should_handle(self, event_type: str) -> bool:
        """Check if this type of event should be handled"""
        return event_type in self._event_types

    def _handle_event(self, event, event_type: str):
        """Unified event handling logic"""
        if not self._should_handle(event_type):
            return

        # Normalize to absolute path in POSIX format (Linux-style forward slashes)
        src_path = Path(event.src_path).absolute().as_posix()

        # Also normalize dest_path
        dest_path = getattr(event, 'dest_path', None)
        if dest_path:
            dest_path = Path(dest_path).absolute().as_posix()

        # Build message body
        body = {
            'event_type': event_type,
            'src_path': src_path,
            'dest_path': dest_path,
            'is_directory': event.is_directory,
            'timestamp': time.time(),
            'file_content': None,
        }

        # Determine the file path to use for ack operations:
        # - moved event: file has been moved to dest_path, use dest_path
        # - deleted event: file has been deleted, file_path is for record only; ack will skip it
        # - other events: use src_path
        if event_type == 'moved' and dest_path:
            file_path_for_ack = dest_path
        else:
            file_path_for_ack = src_path

        # If debounce is enabled, delay task submission
        if self._debounce_seconds is not None and self._debounce_seconds > 0:
            self._debounce_submit(file_path_for_ack, body, event_type)
        else:
            # No debounce, submit directly
            self._do_submit(file_path_for_ack, body, event_type)

    def _do_submit(self, file_path: str, body: dict, event_type: str):
        """
        Actually submit the task

        Args:
            file_path: File path used for ack operations (dest_path for moved events, src_path otherwise)
            body: Message body
            event_type: Event type
        """
        # Optional: read file content (only for small files and only for event types where the file still exists)
        # - created/modified/moved: file exists, can read
        # - deleted: file has been deleted, do not read
        if self._read_file_content and event_type in ('created', 'modified', 'moved'):
            try:
                if os.path.isfile(file_path) and os.path.getsize(file_path) < 1024 * 1024:  # < 1MB
                    body['file_content'] = Path(file_path).read_text(encoding='utf-8')
            except Exception:
                pass

        # Wrap as kw dict and submit
        kw = {
            'body': body,
            'file_path': file_path,
        }
        self._consumer._submit_task(kw)
        self._consumer.logger.debug(f"Captured file event: {event_type} - {file_path}")

    def _debounce_submit(self, file_path: str, body: dict, event_type: str):
        """
        Debounced submission: if a new event arrives within the debounce window, cancel the old timer and restart

        Args:
            file_path: File path used for ack operations (also used as the debounce key)
            body: Message body
            event_type: Event type
        """
        with self._debounce_lock:
            # Cancel any existing timer for this file path
            if file_path in self._debounce_timers:
                old_timer = self._debounce_timers[file_path]
                old_timer.cancel()
                self._consumer.logger.debug(f"Debounce: cancelled old timer - {file_path}")

            # Create a new timer to delay submission
            def delayed_submit():
                with self._debounce_lock:
                    self._debounce_timers.pop(file_path, None)
                self._do_submit(file_path, body, event_type)
                self._consumer.logger.debug(f"Debounce: timer triggered submission - {file_path}")

            timer = threading.Timer(self._debounce_seconds, delayed_submit)
            self._debounce_timers[file_path] = timer
            timer.start()
            self._consumer.logger.debug(f"Debounce: set new timer {self._debounce_seconds}s - {file_path}")
    
    def on_created(self, event):
        self._handle_event(event, 'created')
    
    def on_modified(self, event):
        self._handle_event(event, 'modified')
    
    def on_deleted(self, event):
        self._handle_event(event, 'deleted')
    
    def on_moved(self, event):
        self._handle_event(event, 'moved')


class WatchdogConsumer(AbstractConsumer):
    """
    Watchdog Consumer

    Listens for file system events and automatically consumes them as messages.
    This is an event-driven broker; users do not need to publish messages manually.
    """

    BROKER_KIND = None  # Will be set automatically by the framework

    def custom_init(self):
        super().custom_init()
        # Get configuration from broker_exclusive_config
        config = self.consumer_params.broker_exclusive_config

        # Users must configure the following fields in the decorator's broker_exclusive_config, otherwise an error will occur.
        watch_path = config['watch_path']
        self._patterns = config['patterns']
        self._ignore_patterns = config['ignore_patterns']
        self._ignore_directories = config['ignore_directories']
        self._case_sensitive = config['case_sensitive']
        self._event_types = config['event_types']
        self._recursive = config['recursive']
        # ack_action: 'delete' | 'archive' | 'none'
        self._ack_action = config['ack_action']
        self._read_file_content = config['read_file_content']
        # Debounce time in seconds; None or 0 means no debounce
        self._debounce_seconds = config['debounce_seconds']

        # Determine monitored directory: use watch_path directly; queue_name is only an identifier
        self._queue_dir = Path(watch_path).absolute()
        self._queue_dir.mkdir(parents=True, exist_ok=True)

        # Archive directory configuration (only needed in archive mode)
        self._archive_dir = None
        if self._ack_action == 'archive':
            archive_path = config['archive_path']
            if not archive_path:
                raise ValueError("When ack_action='archive', archive_path must be configured")

            self._archive_dir = Path(archive_path).absolute()

            # Validation: archive directory must not be a subdirectory of the monitored directory (would cause duplicate events)
            if self._is_subpath(self._archive_dir, self._queue_dir):
                raise ValueError(
                    f"archive_path must not be a subdirectory of watch_path!\n"
                    f"  watch_path: {self._queue_dir.as_posix()}\n"
                    f"  archive_path: {self._archive_dir.as_posix()}\n"
                    f"Please set archive_path to a path outside the monitored directory."
                )

            self._archive_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Archive directory: {self._archive_dir.as_posix()}")

        self._observer = None

        self.logger.info(
            f"Watchdog Consumer initialized, monitored directory: {self._queue_dir.as_posix()}, "
            f"event types: {self._event_types}, file patterns: {self._patterns}"
        )

    def _dispatch_task(self):
        """
        Core dispatch method.
        Starts the watchdog Observer to listen for file system events.
        """
        # First process any files that already exist in the directory
        self._process_existing_files()
        
        # Create event handler
        event_handler = FunboostEventHandler(
            consumer=self,
            event_types=self._event_types,
            read_file_content=self._read_file_content,
            debounce_seconds=self._debounce_seconds,
            patterns=self._patterns,
            ignore_patterns=self._ignore_patterns,
            ignore_directories=self._ignore_directories,
            case_sensitive=self._case_sensitive,
        )
        
        # Create and start Observer
        self._observer = Observer()
        self._observer.schedule(event_handler, self._queue_dir.as_posix(), recursive=self._recursive)
        self._observer.start()

        self.logger.info(f"Watchdog Observer started, now monitoring: {self._queue_dir.as_posix()}")

        # Keep running without exiting, because _dispatch_task is called in an infinite loop by the parent class
        while True:
            time.sleep(100)


    def _process_existing_files(self):
        """Process files that already exist when the service starts"""
        # If event_types does not include 'existing', skip processing pre-existing files
        if 'existing' not in self._event_types:
            return
        
        if not self._queue_dir.exists():
            return
        
        if self._recursive:
            all_items = list(self._queue_dir.rglob('*'))
        else:
            all_items = list(self._queue_dir.glob('*'))
        
        # Filter: keep only files that match the file pattern
        existing_files = []
        for file_path in all_items:
            # Exclude directories
            if not file_path.is_file():
                continue
            # Check if the pattern matches (use full path, consistent with PatternMatchingEventHandler behavior)
            if not self._match_patterns(file_path.absolute().as_posix()):
                continue
            existing_files.append(file_path)

        if existing_files:
            self.logger.info(f"Found {len(existing_files)} files pending processing")
        
        for file_path in existing_files:
            body = {
                'event_type': 'existing',
                'src_path': file_path.absolute().as_posix(),
                'dest_path': None,
                'is_directory': False,
                'timestamp': time.time(),
                'file_content': None,
            }
            
            if self._read_file_content:
                try:
                    if file_path.stat().st_size < 1024 * 1024:
                        body['file_content'] = file_path.read_text(encoding='utf-8')
                except Exception:
                    pass
            
            kw = {
                'body': body,
                'file_path': file_path.absolute().as_posix(),
            }
            self._submit_task(kw)
    
    @staticmethod
    def _is_subpath(child: Path, parent: Path) -> bool:
        """Check whether child is a subdirectory of parent"""
        try:
            child.relative_to(parent)
            return True
        except ValueError:
            return False

    def _match_patterns(self, file_path: str) -> bool:
        """
        Check whether the file path matches the patterns (consistent with PatternMatchingEventHandler behavior)

        Args:
            file_path: Full path of the file (POSIX format)
        """
        # If case-insensitive, normalize to lowercase for comparison
        if not self._case_sensitive:
            path_cmp = file_path.lower()
            patterns = [p.lower() for p in self._patterns]
            ignore_patterns = [p.lower() for p in self._ignore_patterns]
        else:
            path_cmp = file_path
            patterns = self._patterns
            ignore_patterns = self._ignore_patterns

        # First check if the path matches any ignore patterns
        for pattern in ignore_patterns:
            if fnmatch(path_cmp, pattern):
                return False

        # Then check if the path matches any include patterns
        if patterns == ['*']:
            return True
        for pattern in patterns:
            if fnmatch(path_cmp, pattern):
                return True
        return False

    def _confirm_consume(self, kw):
        """
        Confirm successful consumption.
        Decides whether to delete the file or move it to the archive directory based on configuration.
        """
        file_path = kw.get('file_path')
        if not file_path or not os.path.exists(file_path):
            return

        try:
            if self._ack_action == 'delete':
                os.unlink(file_path)
                self.logger.debug(f"Consumption confirmed, file deleted: {file_path}")
            elif self._ack_action == 'archive':
                # Move to archive directory, preserving relative path structure
                file_path_obj = Path(file_path)
                # Calculate relative path of the file with respect to the monitored directory
                relative_path = file_path_obj.relative_to(self._queue_dir)
                # Preserve the same relative path in the archive directory
                dest = self._archive_dir / relative_path
                # Ensure destination directory exists
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(file_path, dest.as_posix())
                self.logger.debug(f"Consumption confirmed, file archived to: {dest.as_posix()}")
            else:
                # ack_action == 'none', pure monitoring mode
                self.logger.debug(f"Consumption confirmed, pure monitoring mode, file left in place: {file_path}")
        except Exception as e:
            self.logger.warning(f"Failed to process file during consumption confirmation: {e}")

    def _requeue(self, kw):
        """
        Requeue message (only effective in archive mode).
        Moves the file from the archive directory back to the monitored directory to trigger re-consumption.
        """
        if self._ack_action != 'archive' or not self._archive_dir:
            self.logger.warning("requeue is only effective when ack_action='archive'")
            return

        file_path = kw.get('file_path')
        if not file_path:
            return

        # Calculate relative path of the file with respect to the monitored directory
        file_path_obj = Path(file_path)
        try:
            relative_path = file_path_obj.relative_to(self._queue_dir)
        except ValueError:
            # If relative path cannot be computed, use the filename
            relative_path = file_path_obj.name

        # Check for the corresponding file in the archive directory
        archived_path = self._archive_dir / relative_path
        if archived_path.exists():
            try:
                # Move back to the monitored directory, preserving relative path structure
                dest = self._queue_dir / relative_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(archived_path.as_posix(), dest.as_posix())
                self.logger.info(f"Message requeued, file moved back to: {dest.as_posix()}")
            except Exception as e:
                self.logger.warning(f"Failed to move file during requeue: {e}")


# ============================================================================
# Register Broker
# ============================================================================

BROKER_KIND_WATCHDOG = 'WATCHDOG'


register_broker_exclusive_config_default(
    BROKER_KIND_WATCHDOG,
    {
        'watch_path': './watchdog_queues',      # Root directory to monitor
        'patterns': ['*'],                       # File patterns to match
        'ignore_patterns': [],                   # File patterns to ignore
        'ignore_directories': True,              # Whether to ignore directory events
        'case_sensitive': False,                 # Whether matching is case-sensitive

         # Full list of event_types: ['created', 'modified', 'deleted', 'moved', 'existing']
         # created: file created; modified: file modified; deleted: file deleted; moved: file moved;
         # existing: whether files that already exist at startup trigger funboost consumption;
         #           native watchdog does not support this, but funboost does —
         #           perfectly handles files that accumulated while the funboost service was stopped after a restart
        'event_types': ['created', 'modified'],
        # Event types to listen for. If writing files once, only listen to 'modified';
        # otherwise each new file write triggers both 'created' and 'modified' for a total of 2 events.

        'recursive': False,                      # Whether to recursively monitor subdirectories

        # ack_action options: 'delete' | 'archive' | 'none'
        # delete: delete file after consumption; archive: archive to archive_path; none: pure monitoring mode, do nothing
        'ack_action': 'delete',              # Action after consumption

        # Archive directory path (only needed when ack_action='archive')
        # Important: archive_path must not be a subdirectory of watch_path, otherwise duplicate events will be triggered!
        'archive_path': None,

        'read_file_content': True,               # Whether to read file content (for files smaller than 1MB)

        # Debounce time in seconds: None means no debounce; setting a value means multiple events on the same file
        # within that time window will only trigger one consumption.
        # Example: debounce_seconds=2 — creating at t=0, modifying at t=1, modifying again at t=2
        # will only trigger consumption once, 2 seconds after the last modification.
        'debounce_seconds': 0.5,
    }
)

register_custom_broker(BROKER_KIND_WATCHDOG, WatchdogPublisher, WatchdogConsumer)


# ============================================================================
# Test Code
# ============================================================================


