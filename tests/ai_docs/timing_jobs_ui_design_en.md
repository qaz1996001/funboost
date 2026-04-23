# Funboost Timing Task Management UI Planning Document

## I. Existing Management Interface Analysis

### 1.1 Current Page Structure
Existing management interface adopts classic **left navigation bar + right content area (iframe)** layout:

**Left Navigation Bar Pages**:
1. Function result table - `fun_result_table.html`
2. Consumption rate chart - `conusme_speed.html`
3. Running consumers (by ip) - `running_consumer_by_ip.html`
4. Running consumers (by queue) - `running_consumer_by_queue_name.html`
5. **Queue Operations** - `queue_op.html` (most complex page, includes tables, charts, modals)
6. RPC call - `rpc_call.html`
7. About - `about.html`

### 1.2 Existing Design Style
- **UI Framework**: Bootstrap 3.3.7
- **Table Tool**: Tabulator 5.5.0
- **Chart Tool**: Chart.js
- **Color Scheme**: Dark color scheme (sidebar: #296074, active state: #0BBAF8)
- **Icons**: Font Awesome 4.7.0
- **Interaction Mode**: Modals as primary, avoid page jumps

## II. Timing Task Management UI Design Proposal ⭐

### 2.1 Recommended Approach: Single Page Integration Mode (Best)

**Core Idea**: Integrate all timing task management functions in **one page**, similar to existing `queue_op.html`

#### Page Name
`timing_jobs_management.html`

#### Navigation Bar New Item
```
Timing Task Management (Icon: fa-clock-o)
```

#### Page Layout Structure

```
┌─────────────────────────────────────────────────────────┐
│  [Search: Queue/Task ID]  [Filter: All/Running/Paused]  │
│  [Button: Add Task] [Button: Refresh] [Button: Auto-refresh] │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│              Timing Task List Table                      │
│ ┌───────┬────────┬────────┬──────────┬────────┬────────┐ │
│ │Task ID│Queue   │Trigger │Next Run  │Status  │Actions │ │
│ ├───────┼────────┼────────┼──────────┼────────┼────────┤ │
│ │job_001│test_q  │interval│2025-12-11│Running │[Detail]│ │
│ │       │        │10s     │16:45:00  │        │[Pause] │ │
│ │       │        │        │          │        │[Delete]│ │
│ ├───────┼────────┼────────┼──────────┼────────┼────────┤ │
│ │job_002│data_q  │cron    │2025-12-12│Running │[Detail]│ │
│ │       │        │daily 2am│02:00:00 │        │[Pause] │ │
│ │       │        │        │          │        │[Delete]│ │
│ └───────┴────────┴────────┴──────────┴────────┴────────┘ │
│                [Pagination Control]                      │
└─────────────────────────────────────────────────────────┘
```

#### Functional Module Division

##### 1. **Top Operation Bar**
- Search box (supports queue name, task ID search)
- Filter dropdown (All tasks/Running/Paused)
- Queue filter dropdown (dynamically load queue list)
- Add task button (open add task modal)
- Refresh list button
- Auto-refresh toggle switch (10-second auto-refresh)

##### 2. **Task List Table** (Using Tabulator)
| Column | Field | Notes |
|------|------|------|
| Task ID | job_id | Click to copy |
| Queue Name | queue_name | Display queue name |
| Trigger | trigger | interval/cron/date |
| Trigger Params | trigger_params | Show details on hover |
| Next Run Time | next_run_time | Real-time countdown |
| Status | status | Running/Paused |
| Actions | actions | Detail/Edit/Pause/Resume/Delete |

##### 3. **Modal Design**

###### 3.1 Add Task Modal
```
┌────────────────  Add Timing Task  ────────────────┐
│                                                 │
│  Queue Name: [Dropdown Selection] ────────────┐   │
│                                              │   │
│  Task ID: [Input] (Optional, auto-generate)  │   │
│                                              │   │
│  Trigger Type: ○ One-time  ○ Interval ● Cron │   │
│                                              │   │
│  ┌─── Cron Configuration ───────────────┐  │   │
│  │ Year:  [*    ] Month: [*    ] Day: [*   ] │  │   │
│  │ Week:  [     ] Day of Week: [   ] Hour: [9] │  │   │
│  │ Minute:[0    ] Second: [0    ]             │  │   │
│  │                                        │  │   │
│  │ Description: Execute daily at 9am      │  │   │
│  │ Preview: Next run 2025-12-12 09:00:00   │  │   │
│  └────────────────────────────────────────┘  │   │
│                                              │   │
│  Storage Method: ○ Redis (Recommended) ○ Memory│   │
│                                              │   │
│  [Cancel]  [Preview Time]  [Confirm]         │   │
└──────────────────────────────────────────────┘
```

###### 3.2 Task Detail Modal
```
┌────────────────  Task Details  ────────────────┐
│                                             │
│  Task ID: job_test_001                       │
│  Queue Name: test_queue                      │
│  Trigger Type: interval                      │
│  Trigger Params:                             │
│    - seconds: 10                             │
│  Status: Running                             │
│  Created: 2025-12-11 16:30:00                │
│  Next Run: 2025-12-11 16:45:30 (58s left)   │
│  Last Run: 2025-12-11 16:45:20               │
│  Executions: 1,234 times                     │
│  Failed: 5 times                             │
│  Storage Method: redis                       │
│                                             │
│  [Close]  [Edit]  [Delete]                   │
└─────────────────────────────────────────────┘
```

###### 3.3 Bulk Operation Confirmation
```
┌────────  Confirm Delete  ────────┐
│                            │
│  Confirm delete following tasks? │
│                            │
│  • job_001 (test_queue)    │
│  • job_002 (data_queue)    │
│                            │
│  This action cannot be undone!  │
│                            │
│  [Cancel]  [Confirm Delete]     │
└────────────────────────────────┘
```

### 2.2 Alternative Approach: Multi-Page Separation Mode

If single page is too complex, can split into 2 pages:

#### Page 1: `timing_jobs_list.html` - Task List
- Task list table
- Search, filter
- Basic operations (pause, resume, delete)
- Navigation button: [Add Task] jump to add page

#### Page 2: `timing_jobs_add.html` - Add/Edit Task
- Form-style layout
- Configuration interface for three trigger types
- Real-time preview
- Return to list button

**Not recommended** because:
- Increases page jumps, worse user experience than single page
- Inconsistent with existing management interface style (existing pages are single-page design)

### 2.3 Simplest Approach: Integrate Into Queue Operation Page

Add a Tab tag in existing `queue_op.html` page:

```
[Queue List] | [Timing Tasks]
```

**Pros**:
- No need to add new navigation item
- Queue and timing tasks highly related, reasonable to put together

**Cons**:
- Queue operation page already complex, adding timing tasks more bloated
- Not easy to extend and maintain

## III. Recommended Feature List

### 3.1 Basic Features (Required)
✅ View all timing task list
✅ Add timing task (three trigger types)
✅ Delete single task
✅ Pause/Resume task
✅ View task details
✅ Search and filter

### 3.2 Advanced Features (Recommended)
🔶 Bulk delete tasks
🔶 Edit task (delete then add)
🔶 View execution records (if logs exist)
🔶 Next execution time countdown
🔶 Trigger parameter preview and validation
🔶 Task templates (quick add common configurations)

### 3.3 High-Level Features (Optional)
⭕ Task execution history statistics
⭕ Task dependency relationship visualization
⭕ Import/Export task configuration
⭕ Task execution log real-time viewing
⭕ Error retry configuration

## IV. Technical Implementation Key Points

### 4.1 Frontend
- **Table**: Tabulator (consistent with existing queue operation page)
- **Modal**: Bootstrap Modal
- **AJAX**: jQuery (consistent with existing code)
- **Form Validation**: Client-side real-time validation + server-side validation
- **Real-time Update**: Optional 10-second auto-refresh

### 4.2 Backend Interfaces (Completed)
Implemented 7 interfaces in `flask_blueprint`:
- POST `/funboost/add_timing_job` - Add task
- GET `/funboost/get_timing_jobs` - Get task list
- GET `/funboost/get_timing_job` - Get task details
- DELETE `/funboost/delete_timing_job` - Delete task
- DELETE `/funboost/delete_all_timing_jobs` - Bulk delete
- POST `/funboost/pause_timing_job` - Pause task
- POST `/funboost/resume_timing_job` - Resume task

### 4.3 Data Flow
```
User Operation → Frontend Event → AJAX Request → Flask Blueprint 
→ ApsJobAdder → APScheduler → Redis/Memory
```

## V. UI/UX Design Key Points

### 5.1 User Friendliness
1. **Smart Form**:
   - Automatically load queue information after selecting queue
   - Dynamically show corresponding configuration items when trigger type switches
   - Real-time preview next run time when entering parameters

2. **Operation Feedback**:
   - All operations have loading status hints
   - Both success/failure have clear message prompts
   - Dangerous operations (delete) require confirmation

3. **Data Visualization**:
   - Use color to distinguish status (Running=green, Paused=yellow)
   - Next execution time shows countdown
   - Trigger parameters described in human-friendly language

### 5.2 Consistency Maintenance
- Button style consistent with queue operation page
- Table color scheme consistent with existing table
- Modal layout consistent with existing modals
- Use Font Awesome 4.7.0 icons

### 5.3 Responsive Design
- Table supports horizontal scrolling (when many columns)
- Modal adapts on small screens
- Action buttons stack on small screens

## VI. Development Suggestions

### 6.1 Phased Implementation

**Phase 1: MVP (Minimum Viable Product)**
1. Task list display
2. Add task (three trigger types)
3. Delete task
4. Basic search

**Phase 2: Feature Completion**
5. Pause/Resume task
6. Task detail viewing
7. Advanced filtering
8. Auto-refresh

**Phase 3: Experience Optimization**
9. Parameter preview and validation
10. Bulk operations
11. Execution history
12. Error handling optimization

### 6.2 Code Organization
```
timing_jobs_management.html
├── HEAD: Import CSS/JS
├── BODY:
│   ├── Top operation bar
│   ├── Task list table (Tabulator)
│   ├── Add task modal
│   ├── Task detail modal
│   └── Various confirmation dialogs
└── SCRIPT:
    ├── Tabulator initialization
    ├── Modal control
    ├── AJAX request wrapper
    └── Utility functions (time formatting, etc.)
```

## VII. Summary and Recommendations

### Recommended Implementation Approach
**Single Page Integration Mode** (`timing_jobs_management.html`)

### Recommended Reasons
1. ✅ Conforms to existing management interface design pattern
2. ✅ Smooth user experience, no page jumps
3. ✅ Easy to maintain and extend
4. ✅ Can reuse existing CSS/JS components
5. ✅ Consistent style with queue operation page

### Core Features
- **One navigation item**: Timing Task Management
- **One page file**: timing_jobs_management.html
- **Three main modals**: Add task, task details, confirmation
- **One table**: Tabulator task list
- **Seven backend interfaces**: Completed (Flask Blueprint)

### Expected Result
Users can complete all timing task management operations in one page without jumps, smooth experience, completely consistent with existing management interface style.

---

## Appendix: Reference Examples

### Cron Expression Friendly Tips
```javascript
const cronExamples = {
    'Daily 9am': { hour: '9', minute: '0', second: '0' },
    'Every 2 hours': { hour: '*/2', minute: '0', second: '0' },
    'Weekday 10am': { day_of_week: '0-4', hour: '10', minute: '0' },
    'First of month 2am': { day: '1', hour: '2', minute: '0' }
};
```

### Trigger Type Description
```
date: One-time task, execute once at specified time then auto-delete
interval: Interval task, repeat at fixed intervals
cron: Scheduled task, execute according to Cron expression
```

### Status Color Specification
```css
.status-running { background-color: #4CAF50; } /* Green */
.status-paused { background-color: #FF9800; }  /* Orange */
.status-error { background-color: #F44336; }   /* Red */
```
