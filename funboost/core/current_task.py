"""
fct is short for funboost current task, meaning the current task. It supports both threading and asyncio isolation.

fct usage example:
'''
from funboost import fct

Inside the consuming function, you can access the task_id, queue_name, etc.
print(fct.function_result_status.get_status_dict())
print(fct.function_result_status.task_id)
print(fct.run_times)
print(fct.full_msg)
'''


"""

import typing
import contextvars
from dataclasses import dataclass
import logging
import threading


from funboost.core.function_result_status_saver import FunctionResultStatus

@dataclass
class FctContext:
    """
    fct is short for funboost current task
    """
    function_result_status: FunctionResultStatus
    logger: logging.Logger
    # asyncio_use_thread_concurrent_mode: bool = False # This attribute is deprecated, now contextvars is used regardless of concurrency mode

# Use contextvars to uniformly manage context, contextvars supports both multithreading and async coroutine scenarios
_fct_context_var: contextvars.ContextVar[typing.Optional[FctContext]] = contextvars.ContextVar('fct_context', default=None)


def set_fct_context(fct_context: typing.Optional[FctContext]):
    """Set the FctContext for the current thread/coroutine"""
    _fct_context_var.set(fct_context)


def get_fct_context() -> FctContext:
    """Get the FctContext for the current thread/coroutine"""
    return _fct_context_var.get()


class _FctProxy:
    """
    fct proxy class, automatically retrieves current thread/coroutine context via contextvars.
    You can directly import fct, no need to manually write fct = funboost_current_task().
    Just use `from funboost import fct`.
    funboost's fct is similar to Flask's request object, with automatic thread/coroutine-level isolation, multiple threads won't interfere with each other.


    fct is slightly more convenient than direct get_fct_context, as fct promotes many important second-level attributes from function_result_status to first-level attributes.
    """

    @property
    def fct_context(self) -> FctContext:
        return get_fct_context()

    @property
    def logger(self) -> logging.Logger:
        return self.fct_context.logger

    # The properties below are second-level attributes of function_result_status, promoted to first-level for convenience.
    # You can still access more attributes through fct.function_result_status
    @property
    def function_params(self) -> dict:
        return self.fct_context.function_result_status.params

    @property
    def full_msg(self) -> dict:
        return self.fct_context.function_result_status.msg_dict

    @property
    def function_result_status(self) -> FunctionResultStatus:
        return self.fct_context.function_result_status

    @property
    def task_id(self) -> str:
        return self.fct_context.function_result_status.task_id
    @property
    def queue_name(self) -> str:
        return self.fct_context.function_result_status.queue_name

    def __str__(self):
        return f'<{self.__class__.__name__} [{self.function_result_status.get_status_dict()}]>'


fct = _FctProxy() # Recommended to use this fct object. fct is short for funboost_current_task, meaning the current message task.


def funboost_current_task() -> _FctProxy:
    """
    This is for backward compatibility with the old funboost_current_task() function, now just use fct directly.

    Get the current task context proxy object.
    Since contextvars supports both multithreading and async coroutines, simply return the fct proxy object.
    """
    return fct


def get_current_taskid() -> str:
    """Get the task_id of the current task"""
    try:
        ctx = get_fct_context()
        if ctx is None:
            return 'no_task_id'
        return ctx.function_result_status.task_id
    except (AttributeError, LookupError):
        return 'no_task_id'


class FctContextThread(threading.Thread):
    """
    This class automatically propagates the current thread's funboost context to newly spawned threads.
    Since contextvars don't automatically propagate across threads (only across coroutines), manual context copying is needed for cross-thread propagation.


    Without this base class, you would need to manually copy the context and run ctx.run(worker) instead of worker directly:
    # 1. Explicitly capture current context
    ctx = contextvars.copy_context()
    # 2. Let the thread run ctx.run(worker) instead of worker directly
    # This way worker executes within ctx's context
    t = threading.Thread(target=ctx.run, args=(worker,)) # This is correct, propagates context

    # t = threading.Thread(target=worker,args=(,)) # This is wrong, cannot auto-propagate context to child thread,
    # For example funboost's timeout kill feature runs consuming functions in separate child threads, so context propagation to child threads is sometimes needed.

    """

    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, *, daemon=None):
        super().__init__(group=group, target=target, name=name,
                         args=args, kwargs=kwargs, daemon=daemon)
        # self._fct_context = get_fct_context() # This only targets ct

        # 1. Core change: capture a snapshot of all current contextvars context,
        # This is more general-purpose, not just for fct_context, but also for all other contextvars contexts, such as OpenTelemetry's
        self._ctx = contextvars.copy_context()

    def run(self):
        # set_fct_context(self._fct_context) # This only targets fct_context; other contextvars contexts will not be propagated.
        # super().run()

        # 2. Core change: run super().run() within the captured context
        # This is more general-purpose, allowing all code inside run to access the parent thread's OTel TraceID and fct
        return self._ctx.run(super().run)



if __name__ == '__main__':
    print(get_current_taskid())
