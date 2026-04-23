# Changes Based on Third-party func_timeout Package

The main changes are that `StoppableThread` and `JoinThread` now inherit from `FctContextThread` instead of `threading.Thread`.

The reason for this is to support passing the current thread's funboost context to the separate timeout thread, making it convenient to use the funboost context `funboost_current_task` even after setting a timeout.
