# Background commands

## .delay()

Calling `.delay()` on a `PipePy` instance returns a copy that starts running in the background. Accessing its output waits for it to finish.

```python
from pipepy import wget
urls = [...]

# All downloads will happen in the background simultaneously
downloads = [wget(url).delay() for url in urls]

# Do something else while downloads work

# This will call __bool__ on all downloads and thus wait for them
if not all(downloads):
   print("Some downloads failed")
```

## .wait()

If you're not interested in the output, call `.wait()` to ensure the process completes before the parent exits.

```python
from pipepy import wget
download = wget('...').delay()
# Do something else
download.wait()
```

## Timeout

Supply optional `timeout` argument to `wait`. If the timeout expires before the process finishes, a `TimeoutExpired` exception is raised.

```python
from pipepy import sleep
command = sleep(100).delay()
command.wait(5)
# <<< TimeoutExpired: Command '['sleep', '30']' timed out after 5 seconds
```

## Tracking jobs

At any point, call `pipepy.jobs()` to get a list of non-waited-for commands. `pipepy.wait_jobs()` cleans up all background jobs.

```python
from pipepy import jobs, wait_jobs

# Get list of pending background commands
pending = jobs()

# Wait for all of them
wait_jobs()

# With timeout
wait_jobs(timeout=10)
```

Use `wait_jobs` with care — if any background job is stuck, it may hang. `wait_jobs` accepts optional `timeout` argument.
