# Funboost Timing Task Management Interface Usage Guide

## Functionality Complete!

Timing task management has been fully integrated into Funboost management interface!

## Created/Modified Files

### 1. New Files
- `funboost/funboost_web_manager/templates/timing_jobs_management.html` - Timing task management page

### 2. Modified Files
- `funboost/funboost_web_manager/templates/index.html` - Add "Timing Task Management" menu item to navigation
- `funboost/funboost_web_manager/app.py` - Already registered flask_blueprint (you added)
- `funboost/faas/flask_adapter.py` - Added 7 timing task interfaces

## How to Use

### Start Service

You've already registered `flask_blueprint` in `app.py`, so just start Flask service directly:

```python
from funboost.funweb.app import start_funboost_web_manager

start_funboost_web_manager(
    host="0.0.0.0",
    port=27018,
    debug=False
)
```

Or directly run:
```bash
python -m funboost.funweb.app
```

### Access Interface

1. Open browser and visit: `http://localhost:27018`
2. Login with account (admin/123456 or user/mtfy123)
3. Click **"Timing Task Management"** menu item in left navigation (clock icon)

## Feature Description

### 1. Task List
- Show all timing tasks
- Support search by queue name and task ID
- Support filtering by queue
- Auto-refresh functionality (10-second interval)

### 2. Add Task
Click **"Add Task"** button, supports three trigger types:

#### One-Time Task (date)
```
Trigger: date
Run Time: 2025-12-15 10:00:00
Description: Execute once at specified time then auto-delete
```

#### Interval Execution (interval)
```
Trigger: interval
Example 1: Every 10 minutes → Minute: 10
Example 2: Every 2 hours → Hour: 2
Example 3: Daily → Day: 1
```

#### Scheduled Execution (cron)
```
Trigger: cron
Example 1: Every day 9am → Hour:9 Minute:0 Second:0
Example 2: Every 2 hours → Hour:*/2 Minute:0
Example 3: Weekday 10am → Day of Week:0-4 Hour:10 Minute:0

Cron Syntax:
* = Any value
*/n = Every n units
1-5 = Range
1,3,5 = List
```

### 3. Task Operations
Each task can perform following operations:
- **Details**: View task details
- **Pause**: Pause task execution
- **Delete**: Delete task (irreversible)

### 4. Bulk Operations
- **Delete All Tasks**: Can delete tasks from specific queue or all queues

## Interface Features

### 1. Completely Consistent with Existing Interface
- Use same Bootstrap 3.3.7 theme
- Use same Tabulator 5.5.0 table
- Use same color scheme and icons
- Use same modal interaction pattern

### 2. Friendly User Experience
- Smart form: Dynamically show configuration items based on trigger type
- Real-time validation: Validate required items before adding task
- Operation confirmation: Dangerous operations (delete) require second confirmation
- Status hints: All operations have success/failure prompts

### 3. Responsive Design
- Table supports horizontal scrolling
- Pagination display, default 50 items per page
- Support sorting and search

## Data Flow

```
User Operation → Frontend Page → AJAX Request 
→ Flask Blueprint (/funboost/*) 
→ ApsJobAdder 
→ APScheduler 
→ Redis/Memory
```

## Tech Stack

| Layer | Tech |
|------|------|
| Frontend Framework | Bootstrap 3.3.7 |
| Table Component | Tabulator 5.5.0 |
| Icon Library | Font Awesome 4.7.0 |
| AJAX | jQuery 1.11.0 |
| Backend Framework | Flask |
| Backend Interface | Flask Blueprint |
| Timing Task | APScheduler |
| Task Storage | Redis / Memory |

## Interface List

All interfaces under `/funboost/` path:

| Method | Path | Notes |
|------|------|------|
| POST | /funboost/add_timing_job | Add timing task |
| GET | /funboost/get_timing_jobs | Get task list |
| GET | /funboost/get_timing_job | Get task details |
| DELETE | /funboost/delete_timing_job | Delete task |
| DELETE | /funboost/delete_all_timing_jobs | Delete all tasks |
| POST | /funboost/pause_timing_job | Pause task |
| POST | /funboost/resume_timing_job | Resume task |

## Usage Examples

### Example 1: Data Sync Every 10 Minutes
```
Queue Name: data_sync_queue
Trigger Type: interval
Minutes: 10
Storage Method: Redis
```

### Example 2: Backup Daily at 2am
```
Queue Name: backup_queue
Trigger Type: cron
Hour: 2
Minute: 0
Second: 0
Storage Method: Redis
```

### Example 3: Send Notification Tomorrow 10am
```
Queue Name: notification_queue
Trigger Type: date
Run Time: 2025-12-12 10:00:00
Storage Method: Redis
```

## Precautions

### 1. Queue Must Exist
Ensure queue is registered via `@boost` decorator before adding timing task.

### 2. Storage Method Choice
- **Redis** (Recommended): Supports distribution, task persistence, multi-process sharing
- **Memory**: Memory storage only, tasks lost on process restart, suitable for testing

### 3. Task ID
- Leave empty to auto-generate
- Custom naming recommended to be meaningful
- Same ID will override (need to check "Replace" option)

### 4. Timezone Setting
Default uses system timezone, can configure in `funboost_config.py`:
```python
from funboost.funboost_config_deafult import FunboostCommonConfig
FunboostCommonConfig.TIMEZONE = 'Asia/Shanghai'
```

### 5. Distributed Deployment
When multiple processes use same Redis storage, task only executes once (auto-deduplication).

## Common Questions

### Q1: Task doesn't execute after adding?
**A**: Check following:
1. Ensure consumer process is running
2. Check if task's next run time is correct
3. Check consumer logs for errors

### Q2: Task ID entered wrong?
**A**: Delete task and re-add, or check "Replace" option to re-add same ID task

### Q3: How to view task execution history?
**A**: Current version doesn't support, can view consuming function execution logs

### Q4: Can modify existing task?
**A**: Currently not directly supported, need to delete then re-add, or check "Replace" option to re-add same ID task

## Related Documentation

- [Interface Usage Documentation](./flask_timing_job_api_usage.md)
- [UI Design Documentation](./timing_jobs_ui_design.md)

## Completion Checklist

✅ Timing task management page (`timing_jobs_management.html`)
✅ Navigation menu item (clock icon)
✅ 7 backend interfaces (Flask Blueprint)
✅ Task list table (Tabulator)
✅ Add task modal (three trigger types)
✅ Task detail viewing
✅ Pause/Delete task
✅ Bulk delete task
✅ Search and filter functionality
✅ Auto-refresh functionality
✅ Completely consistent with existing style

---

## Ready to Use Now!

Start Flask service, visit management interface, click "Timing Task Management" menu, start managing your timing tasks! 🎉
