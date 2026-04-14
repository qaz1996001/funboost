# -*- coding: utf-8 -*-
"""
Test Watchdog File System Monitor Broker

Watchdog Broker is an event-driven middleware:
1. No need to manually publish messages
2. File creation/modification automatically triggers consumption
3. Suitable for file processing pipeline scenarios
4. Demonstrates that in funboost, anything can be a broker;
   funboost has extremely high and unlimited extensibility
"""

import time
from pathlib import Path


from funboost import boost, BoosterParams, ctrl_c_recv, BrokerEnum


# Test directory
TEST_DIR = Path(__file__).parent / "watchdog_test_data"
# Archive directory (must be outside the monitored directory)
ARCHIVE_DIR = Path(__file__).parent / "watchdog_archive"


@boost(
    BoosterParams(
        queue_name="test_file_processor",
        broker_kind=BrokerEnum.WATCHDOG,
        qps=10,
        concurrent_num=3,
        broker_exclusive_config={
            # ==================== Required configuration ====================
            "watch_path": TEST_DIR.absolute().as_posix(),  # Monitored directory path (must use absolute POSIX format)

            # ==================== File matching configuration ====================
            "patterns": ["*.txt", "*.json", "*.csv", "*.msg"],  # File patterns to match; ['*'] means all files
            "ignore_patterns": [],               # File patterns to ignore, e.g. ['*.tmp', '*.log']
            "ignore_directories": True,          # Whether to ignore directory events
            "case_sensitive": False,             # Whether filename matching is case-sensitive

            # ==================== Event type configuration ====================
            # event_types enum: ['created', 'modified', 'deleted', 'moved', 'existing']
            # - created: file newly created
            # - modified: file modified
            # - deleted: file deleted
            # - moved: file moved/renamed
            # - existing: files already present at startup (not natively supported by watchdog; extended by funboost)
            "event_types": [
                "created",   # If only listening to modified, a single-write file only triggers 1 event; listening to both created+modified triggers 2 events
                "existing",  # Perfectly handles files accumulated during service downtime before funboost restarts
                "modified",
            ],

            # ==================== Directory recursion configuration ====================
            "recursive": True,                  # Whether to recursively monitor subdirectories

            # ==================== Consumption acknowledgment configuration ====================
            # ack_action enum: 'delete' | 'archive' | 'none'
            # - delete: delete the file after successful consumption
            # - archive: move the file to the directory specified by archive_path after successful consumption
            # - none: monitoring only; no action taken
            "ack_action": "archive",

            # ==================== Archive directory configuration ====================
            # Only needed when ack_action='archive'
            # Important: archive_path must NOT be a subdirectory of watch_path!
            "archive_path": ARCHIVE_DIR.absolute().as_posix(),

            # ==================== File content reading ====================
            "read_file_content": True,           # Whether to automatically read file content (only for files smaller than 1MB)

            # ==================== Debounce configuration ====================
            # debounce_seconds: None | float
            # - None: no debounce; every file event triggers consumption
            # - float: debounce time (seconds); multiple events for the same file within this window trigger only one consumption
            # Example: debounce_seconds=2 — file created at 0s, modified at 1s, modified again at 2s;
            #          only one consumption is triggered 2 seconds after the last modification
            "debounce_seconds": 30,               # 2-second debounce; multiple operations on the same file in a short time trigger only once
        },
        should_check_publish_func_params=False,
    )
)
def process_file(   # The function parameters are fixed to these.
    event_type,
    src_path,
    dest_path,
    is_directory,
    timestamp,
    file_content,
):
    print(locals())
    """Process file event"""
    print(f"[{event_type}] Processing file: {src_path}")
    if file_content:
        preview = (
            file_content[:500] + "..." if len(file_content) > 500 else file_content
        )
        print(f"  Content preview: {preview}")
    time.sleep(0.3)
    return f"Processing complete: {Path(src_path).name}"


def create_test_files():
    """Create test files to trigger file creation and file modification events"""
    pending_dir = TEST_DIR
    pending_dir.mkdir(parents=True, exist_ok=True)

    print(f"Creating test files in: {pending_dir}")

    for i in range(5):
        file_path = pending_dir / f"test_file_{i}.txt"
        file_path.write_text(f"This is test file {i}\nContent line 1\nContent line 2", encoding="utf-8")
        print(f"  Created: {file_path.name}")

    print(f"5 test files created")


def manual_push():
    """
    When watchdog is used as a broker, funboost allows manually publishing messages.
    However, manual publishing is not required; the mechanism is that watchdog automatically
    triggers the consumer function when it detects file changes, so there is no need to
    call push manually.
    """
    for i in range(3):
        process_file.push(a=i, b=i * 2)


if __name__ == "__main__":
    process_file.consume()
    time.sleep(5)
    create_test_files()
    manual_push()
    ctrl_c_recv()
