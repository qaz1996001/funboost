# Funboost Workflow - Declarative Task Orchestration

> A declarative task orchestration API similar to Celery Canvas, making workflow definitions simpler and more intuitive.

## 🚀 Quick Start

```python
from funboost import boost
from funboost.workflow import chain, group, chord, WorkflowBoosterParams

# 1. Define tasks using WorkflowBoosterParams
@boost(WorkflowBoosterParams(queue_name='download_task'))
def download(url):
    return f'/downloads/{url}'

@boost(WorkflowBoosterParams(queue_name='process_task'))
def process(file_path, resolution='360p'):
    return f'{file_path}_{resolution}'

@boost(WorkflowBoosterParams(queue_name='notify_task'))
def notify(results, url):
    return f'Done: {url} -> {results}'

# 2. Build the workflow (declarative)
workflow = chain(
    download.s('video.mp4'),
    chord(
        group(process.s(resolution=r) for r in ['360p', '720p', '1080p']),
        notify.s(url='video.mp4')
    )
)

# 3. Execute
result = workflow.apply()
```

## For more details, see funboost Tutorial Chapter 4b.8 — **Funboost Declarative Task Orchestration Workflow**
