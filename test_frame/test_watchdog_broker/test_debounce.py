# -*- coding: utf-8 -*-
"""
Test Watchdog Broker's debounce functionality

Debounce functionality description:
- debounce_seconds=None: no debounce; every file event triggers consumption
- debounce_seconds=2: 2-second debounce; multiple events on the same file within 2 seconds trigger only one consumption

Test scenario:
1. Create file at second 0
2. Modify file at second 0.5
3. Modify file again at second 1
If debounce_seconds=2 is set, the above operations trigger only 1 consumption (2 seconds after the last modification).
"""

import time
from pathlib import Path
from funboost import boost, BoosterParams, ctrl_c_recv, BrokerEnum

# Test directory
TEST_DIR = Path(__file__).parent / "debounce_test_data"

# Track the number of triggers
trigger_count = 0


@boost(
    BoosterParams(
        queue_name="test_debounce_processor",
        broker_kind=BrokerEnum.WATCHDOG,
        qps=10,
        concurrent_num=3,
        broker_exclusive_config={
            "watch_path": TEST_DIR.absolute().as_posix(),
            "patterns": ["*.txt"],
            "ignore_patterns": [],
            "ignore_directories": True,
            "case_sensitive": False,
            "event_types": ["created", "modified"],  # Listen to both created and modified events
            "recursive": False,
            "ack_action": "none",  # Monitoring only; do not delete files, for easy observation
            "read_file_content": True,
            # ==================== Debounce configuration ====================
            # Set to 2-second debounce
            # If set to None, every file event triggers consumption
            "debounce_seconds": 2,
        },
        should_check_publish_func_params=False,
    )
)
def process_file_debounce(
    event_type,
    src_path,
    dest_path,
    is_directory,
    timestamp,
    file_content,
):
    """Process file event (with debounce)"""
    global trigger_count
    trigger_count += 1
    print(f"\n{'='*60}")
    print(f"[Trigger count: {trigger_count}] [{event_type}] File: {Path(src_path).name}")
    print(f"  Timestamp: {time.strftime('%H:%M:%S', time.localtime(timestamp))}")
    if file_content:
        print(f"  Content: {file_content[:100]}")
    print(f"{'='*60}\n")
    return f"Processing complete: {Path(src_path).name}"


def test_debounce():
    """
    Test the debounce effect.

    Perform multiple rapid operations on the same file and observe whether
    only one consumption is triggered.
    """
    TEST_DIR.mkdir(parents=True, exist_ok=True)

    print("\n" + "="*60)
    print("Starting debounce test (debounce_seconds=2)")
    print("="*60)

    test_file = TEST_DIR / "debounce_test.txt"

    # Second 0: create the file
    print(f"\n[{time.strftime('%H:%M:%S')}] Creating file...")
    test_file.write_text("Version 1: initial content", encoding="utf-8")

    # Second 0.5: modify the file
    time.sleep(0.5)
    print(f"[{time.strftime('%H:%M:%S')}] Modification 1...")
    test_file.write_text("Version 2: first modification", encoding="utf-8")

    # Second 1: modify again
    time.sleep(0.5)
    print(f"[{time.strftime('%H:%M:%S')}] Modification 2...")
    test_file.write_text("Version 3: second modification", encoding="utf-8")

    # Second 1.5: third modification
    time.sleep(0.5)
    print(f"[{time.strftime('%H:%M:%S')}] Modification 3...")
    test_file.write_text("Version 4: third modification", encoding="utf-8")

    print(f"\n[{time.strftime('%H:%M:%S')}] Completed 4 file operations (1 creation + 3 modifications)")
    print("If debounce is working, only 1 consumption should be triggered (2 seconds after the last modification)")
    print(f"Expected trigger time: {time.strftime('%H:%M:%S', time.localtime(time.time() + 2))}")
    print("Waiting for debounce timer to fire...\n")


if __name__ == "__main__":
    process_file_debounce.consume()
    time.sleep(3)  # Wait for the consumer to start
    test_debounce()
    print("\nWaiting to observe results (press Ctrl+C to exit after about 10 seconds)...\n")
    ctrl_c_recv()
