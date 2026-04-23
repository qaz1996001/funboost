

Task: Add a "Universal Log Viewer" module under the `System Functions` section of funweb

## I. Background and Objectives

Currently, funweb already has script deployment management functionality, which includes log viewing for deployed scripts (/deploy/<name>/logs), but its log sources are limited to log files automatically generated during deployment (such as {deployment_name}.nohup.log) with fixed log paths. Now we need to extend a universal log viewer that allows users to:

- Configure multiple commonly-used log folder paths (stored in Redis)

- Browse the list of log files in folders (filename, size, modification time)

- Support wildcard search in filenames (e.g., app*.log.*)

- View content of any log file with support for keyword filtering and time range filtering

- Push log content in real-time through WebSocket (similar to tail -f) instead of polling for refresh

This functionality should be independent of the existing script deployment module, but can reference the existing log viewing interface in terms of interaction methods.

## II. Detailed Function Requirements

### 2.1 Log Folder Management

Users can add, delete, and view commonly-used log folder paths (absolute paths).

Configuration information is stored in Redis with the structure:

Key: funweb:{$ip}:log_folders (set) (because each machine's configuration needs to be isolated)

Each element is the absolute path of a folder (string)



### 2.2 File Browsing

After users select a configured folder, all files and subfolders in that folder are displayed.

The file list should include: filename, last modification time, file size (in human-readable format, such as 12.3 MB).

Support searching by filename (input box supporting * wildcards, e.g., *.log matches all .log files, app*.log.* matches app1.log.20260323, etc.). Searching is performed server-side (using fnmatch or glob).

Clicking a filename enters the log viewer.
Clicking a subfolder allows navigation to browse files and subfolders within it.

### 2.3 Log Content Viewing

Display content of a specified log file with support for the following advanced filtering:

- Keyword filtering: display only lines containing the specified string (case-insensitive)

- Time range filtering: filter based on timestamps at the beginning of log lines (need to parse common formats), users can specify start and end times (e.g., 2025-03-20 10:00:00 to 2025-03-20 11:00:00)

- Real-time mode: receive newly added file content in real-time through WebSocket connection (similar to tail -f). Users can enable/disable real-time mode at any time.

- Display the most recent 200 lines by default (configurable)

- For very large files (over 50MB), limit the number of lines loaded at once, support pagination or on-demand loading (reference the existing deployment log viewer's binary search approach)

### 2.4 Security

The backend must validate that the folder path selected by users is in the configured list (prevent path traversal attacks).

Only allow reading files within the configured list, prohibit access to system sensitive directories (such as /etc, /root, or sensitive directories on Windows drives) or symbolic links pointing outside the directory (optional).

For WebSocket connections, path legitimacy must be verified as well.

## III. Technical Plan

### 3.1 Backend

Flask framework, add new blueprint log_bp and mount it to app (reference the writing style of script_deploy.py and system_monitor.py).

Store configuration in Redis (funweb:{$ip}:log_folders set).




### 3.2 Frontend

Add new page: templates/log_viewer.html, integrate into the existing management interface (add "Log Viewer" entry to left navigation bar).

Use Bootstrap and jQuery (consistent with existing frontend style).

Use Socket.IO client library to receive real-time logs.



Progressive optimizations:

1. Log files should be sortable by creation time, modification time, size, and file type
2. Don't display all files at once on the left side, it makes the webpage too slow.
3. The search file input on the left should prompt users to enter glob wildcard syntax, otherwise users might think fuzzy search without * is supported
4. The date-time picker on the right should default to pre-filled with current time minus 60 minutes to now, but should not trigger a query. The query should be triggered by the quick time range buttons below to avoid users having to manually select time ranges each time.
5. I want to change to fuzzy search, so users don't need to enter *task* wildcards, they can just type task to search for task-related logs.
   Users must select a specific log file before log content is displayed on the right side. No need to support searching for keywords and time ranges across multiple files at once, only search the user-selected file.
6. Query bug
   I selected all time ranges, file is /pythonlogs/task6.nohup.log, why can't I find 1236? The file clearly has 1236 in it.

7. Use select2 dropdown search box to display already-added folder paths, instead of displaying all added folder paths vertically at once.
8. Why is the search so slow? A 13MB log file took 5 seconds to search.
   Performance needs to be optimized to millisecond level.
   Why is Linux grep so fast at searching keywords while you're so slow? I'm currently on a Windows computer. You need to be able to search large files quickly on both Linux and Windows.
9. Why don't the quick time selection buttons like "Last 1 minute", "5 minutes" respond when clicked or show highlighting? When highlighted, the button should turn a bright green color.

10. The date-time picker on the right should default to pre-filled with current time minus 60 minutes to now, but should not trigger a query. The query should be triggered by the quick time range buttons below to avoid users having to manually select time ranges each time.
    But don't fill in seconds, fill in precision down to minutes only.

11. Regarding script deployment, when deploying a certain name, can the command add a flag so that Windows and Linux shell or cmd commands can obtain the process through this flag?
    For example, searching for funweb_deploy=task6 would get the process id of the deployment named task6.

    I now noticed that the page shows task6 has stopped, but the task6.nohup.log file is still being written to, indicating it hasn't actually stopped.

12. In script deployment, when all restart and start buttons are not completed and you click on the blank area of the page, the dialog box disappears. I hope it doesn't disappear this way.

13. In script deployment, after all buttons are activated, they should also change to green highlight.

14. When stopping and restarting, I want to display all found and returned process IDs, and the command to stop the process. You use the search funweb_deploy=deployment_name to find the process ID, then kill it.

    Currently I see:
    ```
    Start command: python test_frame/test_web_deploy/task1.py --deploy_flag=8af836b8-ff8a-489e-848a-9f9bca60677b --funweb_deploy=task6b  (stdout/stderr >> "/pythonlogs\task6b.nohup.log")
    ```
    I think you can delete --deploy_flag=uuid now, the uuid doesn't need to be saved to redis either.
    If you can find the process id through the environment variable FUNWEB_DEPLOY=task6b when starting, then use this to kill the related processes, without needing to kill the deployment reference based on the uuid and pid and start time verification saved in redis.

15. The startup and restart of script deployment, the 10-second alive detection setting doesn't seem to work. The dialog returns content very quickly, so the returned logs are old logs from before, with no actual 10-second process alive detection.
    【Handled】Backend `_start_process` adds health check before writing to Redis (every second for `health_secs` seconds, verifying PID is alive); child process wait timeout changed to be configurable (max 60s). List page AJAX `timeout` adjusted based on `health_check_secs`.

16. The log viewer on the details page of script deployment, I hope to remove the automatic refresh selection of interval seconds, and change it to be the same as the log viewer module with real-time log streaming
    【Handled】Details page changed to SSE `/deploy/<name>/logs/stream` (tracking `nohup` logs), toolbar with "Real-time / Stop Real-time" options.

17. The log viewer on the details page of script deployment and the log viewer module, when entering, I hope real-time is enabled by default.
    And to avoid wasting server performance, even if real-time is enabled, it automatically closes after 5 minutes. If users want real-time again, they need to click to open it themselves.
    【Handled】Details page automatically opens real-time after first `loadLogs`; universal log viewer automatically opens real-time after file selection loading is complete. Both client-side auto-close real-time after 5 minutes + server-side stream lasts at most 300 seconds and sends `timeout` event.
