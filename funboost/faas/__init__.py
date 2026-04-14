# funboost/faas/__init__.py

"""
Lazy import mechanism: only imports the corresponding router when the user actually accesses it.
This way, when the user only uses fastapi, it won't fail because flask/django is not installed.
"""

import typing


from funboost.core.active_cousumer_info_getter import (
    ActiveCousumerProcessInfoGetter,
    QueuesConusmerParamsGetter,
    SingleQueueConusmerParamsGetter,
    CareProjectNameEnv,
 )


# Dynamic import configuration: mapping table defines all supported routers
_ROUTER_CONFIG = {
    'fastapi_router': {
        'module': 'fastapi_adapter',
        'attr': 'fastapi_router',
        'package': 'fastapi',
    },
    'flask_blueprint': {
        'module': 'flask_adapter',
        'attr': 'flask_blueprint',
        'package': 'flask',
    },
    'django_router': {
        'module': 'django_adapter',
        'attr': 'django_router',
        'package': 'django-ninja',
    },
}

# Cache for dynamic imports
_cache = {}


def __getattr__(name: str):
    """
    Lazy import mechanism: only imports the corresponding router when the user actually accesses it.
    This way, when the user only uses fastapi, it won't fail because flask/django is not installed.
    """
    # Check if it is a supported router
    if name not in _ROUTER_CONFIG:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
    
    # If already cached, return directly
    if name in _cache:
        return _cache[name]
    
    # Get configuration info
    config = _ROUTER_CONFIG[name]
    
    # Dynamic import
    try:
        module = __import__(
            f"{__package__}.{config['module']}", 
            fromlist=[config['attr']]
        )
        router_obj = getattr(module, config['attr'])
        _cache[name] = router_obj
        return router_obj
    except ImportError as e:
        raise ImportError(
            f"Cannot import {name}, please install {config['package']} first: pip install {config['package']}\n"
            f"Original error: {e}"
        )


# Define __all__ to support from funboost.faas import *
__all__ = [
    'ActiveCousumerProcessInfoGetter',
    'QueuesConusmerParamsGetter',
    'SingleQueueConusmerParamsGetter',
    'CareProjectNameEnv',
    'fastapi_router',
    'flask_blueprint',
    'django_router',
]


# 4. Type checking support (enables PyCharm/VSCode autocompletion)
if typing.TYPE_CHECKING:
    # This is only for IDE inspection, not executed at runtime, so it won't cause errors
    from .fastapi_adapter import fastapi_router 
    from .flask_adapter import flask_blueprint
    from .django_adapter import django_router