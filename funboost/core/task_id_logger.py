import functools

from nb_log import CompatibleLogger
from funboost.core.current_task import get_current_taskid


class TaskIdLogger(CompatibleLogger):
    """
    If you want to use a log template that includes task_id, you must create the logger using:
     LogManager('namexx', logger_cls=TaskIdLogger).get_logger_and_add_handlers(....)
     i.e. you must specify logger_cls=TaskIdLogger; otherwise you need to manually pass extra when logging:
     logger.info(msg, extra={'task_id': task_idxxx})
     """
    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False):
        extra = extra or {}
        if 'task_id' not in extra:
            extra['task_id'] = get_current_taskid()
        if 'sys_getframe_n' not in extra:
            extra['sys_getframe_n'] = 3
        super()._log(level, msg, args, exc_info, extra, stack_info)
