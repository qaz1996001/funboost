### Celery Canvas Complex Orchestration Example

This example demonstrates Celery's chain/group/chord, nesting, map/starmap, error callbacks, retries, and ignore patterns. It supports two modes:

- Single-machine without a broker (default): local eager in-process execution for quick experimentation
- Distributed (recommended): configure Redis/RabbitMQ, start a worker, and observe true parallelism and fault tolerance

#### 1) Install dependencies

```bash
pip install celery[redis]==5.3.6 requests
```

#### 2) Mode A: Local eager mode (no broker required)

Run a flow directly:

```bash
python -m test_frame.test_celery_canvas.run_flow chain_basics
python -m test_frame.test_celery_canvas.run_flow group_chord --urls https://httpbin.org/get https://www.example.com
python -m test_frame.test_celery_canvas.run_flow chord_with_error_callback --numbers 1 2 3 4 5
python -m test_frame.test_celery_canvas.run_flow nested_chain_group --numbers 1 2 3 4 5
python -m test_frame.test_celery_canvas.run_flow map_and_starmap --numbers 1 2 3 4 5
python -m test_frame.test_celery_canvas.run_flow chain_link_error_ignored
python -m test_frame.test_celery_canvas.run_flow complex_mix --urls https://httpbin.org/get https://www.example.com --numbers 1 2 3 4 5
python -m test_frame.test_celery_canvas.run_flow video_pipeline --video-url https://example.com/video.mp4
```

#### 3) Mode B: Distributed worker mode (broker required)

Set environment variables:

```bash
set CELERY_BROKER_URL=redis://127.0.0.1:6379/0
set CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0
```

Start a worker (on Windows, it is recommended to use eventlet/gevent or run on WSL/Linux/Mac):

```bash
celery -A test_frame.test_celery_canvas.celery_app:app worker -l info -Q canvas_default,io,cpu
```

In another terminal, run a flow using the same commands as in step 2.

#### 4) Directory structure

- `celery_app.py`: Application initialization with eager fallback support
- `tasks.py`: Example task set (addition, multiplication, HTTP requests, retries, errors, Ignore, aggregation, etc.)
- `flows.py`: Multiple orchestration examples including chain/group/chord nesting
- `run_flow.py`: Command-line entry point


