# noinspection PyUnresolvedReferences
import atexit

import nb_log
# noinspection PyUnresolvedReferences
from nb_log import nb_print

'''
The set_frame_config import should be placed before all other code imports to prevent other projects from prematurely importing from funboost.funboost_config_deafult.
If using "from funboost import funboost_config_deafult" and accessing its config inside functions, it's fine, but avoid letting other modules import before set_frame_config.
The use_config_form_funboost_config_module() function in the set_frame_config module is the core — it overrides funboost_config_deafult module with the user's funboost_config.py settings.

This comment is only relevant to framework developers, not end users.
'''

__version__ = "54.4"

from funboost.set_frame_config import show_frame_config

# noinspection PyUnresolvedReferences
from funboost.utils.dependency_packages_in_pythonpath import add_to_pythonpath as _  # This adds dependency_packages_in_pythonpath to PYTHONPATH.
from funboost.utils import monkey_patches as _

from funboost.core.loggers import get_logger, get_funboost_file_logger, FunboostFileLoggerMixin, FunboostMetaTypeFileLogger, flogger
from funboost.core.func_params_model import (BoosterParams, BoosterParamsComplete, FunctionResultStatusPersistanceConfig,
                                             TaskOptions, PublisherParams, BoosterParamsComplete)
from funboost.funboost_config_deafult import FunboostCommonConfig, BrokerConnConfig

# from funboost.core.fabric_deploy_helper import fabric_deploy, kill_all_remote_tasks # fabric2 has not yet been adapted for Python 3.12+, so it's not imported here to avoid errors on higher Python versions.
from funboost.utils.paramiko_util import ParamikoFolderUploader

from funboost.consumers.base_consumer import (wait_for_possible_has_finish_all_tasks_by_conusmer_list,
                                              FunctionResultStatus, AbstractConsumer)
from funboost.consumers.empty_consumer import EmptyConsumer
from funboost.core.exceptions import ExceptionForRetry, ExceptionForRequeue, ExceptionForPushToDlxqueue
from funboost.core.active_cousumer_info_getter import ActiveCousumerProcessInfoGetter
from funboost.core.msg_result_getter import HasNotAsyncResult, ResultFromMongo
from funboost.publishers.base_publisher import (TaskOptions,
                                                AbstractPublisher, AsyncResult, AioAsyncResult)
from funboost.publishers.empty_publisher import EmptyPublisher
from funboost.factories.broker_kind__publsiher_consumer_type_map import register_custom_broker
from funboost.core.broker_kind__exclusive_config_default_define import register_broker_exclusive_config_default
from funboost.factories.publisher_factotry import get_publisher
from funboost.factories.consumer_factory import get_consumer

from funboost.timing_job import funboost_aps_scheduler #,ApsJobAdder
from funboost.timing_job.timing_push import ApsJobAdder

from funboost.constant import BrokerEnum, ConcurrentModeEnum

from funboost.core.booster import boost, Booster, BoostersManager
# from funboost.core.get_booster import get_booster, get_or_create_booster, get_boost_params_and_consuming_function
from funboost.core.kill_remote_task import RemoteTaskKiller
from funboost.funboost_config_deafult import BrokerConnConfig, FunboostCommonConfig
from funboost.core.cli.discovery_boosters import BoosterDiscovery

# from funboost.core.exit_signal import set_interrupt_signal_handler
from funboost.core.helper_funs import run_forever

from funboost.utils.ctrl_c_end import ctrl_c_recv
from funboost.utils.redis_manager import RedisMixin
from funboost.concurrent_pool.custom_threadpool_executor import show_current_threads_num

from funboost.core.current_task import funboost_current_task,fct,get_current_taskid





