
"""
This pydantic base class is compatible with pydantic v1, v2, and v3.
It eliminates v2 deprecation warnings for old methods, and prevents v1-era method errors in future v3.
"""
import datetime
import functools
import json
import typing
from collections import OrderedDict
from pydantic import BaseModel
import pydantic


def _patch_for_pydantic_field_deepcopy():
    from concurrent.futures import ThreadPoolExecutor
    from asyncio import AbstractEventLoop

    # noinspection PyUnusedLocal,PyDefaultArgument
    def __deepcopy__(self, memodict={}):
        """
        pydantic default values need deepcopy.
        """
        return self

    # pydantic types need this
    ThreadPoolExecutor.__deepcopy__ = __deepcopy__
    AbstractEventLoop.__deepcopy__ = __deepcopy__
    # BaseEventLoop.__deepcopy__ = __deepcopy__

_patch_for_pydantic_field_deepcopy

def get_pydantic_major_version() -> int:
    version = pydantic.VERSION
    try:
        return int(version.split(".", 1)[0])
    except Exception:
        return -1

if get_pydantic_major_version() == 1:

    class CompatibleModel(BaseModel):
        class Config:
            arbitrary_types_allowed = True
            # allow_mutation = False
            extra = "forbid"
            json_encoders = {
                datetime.datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S")
            }

        def to_json(self, **kwargs):
            return self.json(**kwargs)

        def to_dict(self):
            return self.dict()

elif get_pydantic_major_version() >= 2:
    from pydantic import ConfigDict

    class CompatibleModel(BaseModel):
        model_config = ConfigDict(
            arbitrary_types_allowed=True,
            extra="forbid",
        )

        # pydantic v2 correctly serializes datetime by default, no extra configuration needed

        def to_json(self, **kwargs):
            return self.model_dump_json(**kwargs)

        def to_dict(self):
            return self.model_dump()


# Unified compatibility decorator for root_validator / model_validator
def compatible_root_validator(*, skip_on_failure=True, mode="after"):
    """
    Unifies pydantic v1 and v2 validator syntax, allowing users to access and modify fields uniformly via self.xxx.

    v1: root_validator(skip_on_failure=skip_on_failure) - original signature is (cls, values: dict)
    v2: model_validator(mode=mode) - signature is (self)

    Usage:
        @compatible_root_validator(skip_on_failure=True)
        def check_values(self):
            if self.qps and self.concurrent_num == 50:
                self.concurrent_num = 500
            return self
    """

    def decorator(func):
        if get_pydantic_major_version() == 1:
            from pydantic import root_validator

            # Note: cannot use @functools.wraps(func), otherwise pydantic v1 will detect the original signature (self) and raise an error.
            def v1_wrapper(cls, values: dict):
                # Create a namespace object so users can access fields via self.xxx
                # Also proxies access to the original model class metadata (e.g. __fields__, model_fields)
                class _ValuesNamespace:
                    # Class attribute: stores a reference to the original model class
                    _model_cls = cls
                    _field_keys = set(values.keys())

                    def __init__(self, d: dict):
                        # Store field values into the instance
                        for k, v in d.items():
                            object.__setattr__(self, k, v)

                    def __setattr__(self, name, value):
                        object.__setattr__(self, name, value)

                    def keys(self):
                        return self._field_keys

                    @property
                    def model_fields(self):
                        # Proxy access to the class field definitions (v2-style compatible)
                        # In v1, returns __fields__
                        return self._model_cls.__fields__

                    def __getattr__(self, name):
                        # Handle access to special attributes like __fields__
                        if name == "__fields__":
                            return self._model_cls.__fields__
                        raise AttributeError(
                            f"'{self._model_cls.__name__}' object has no attribute '{name}'"
                        )

                    @property
                    def __class__(self):
                        # Make self.__class__.__name__ return the correct class name
                        return self._model_cls

                ns = _ValuesNamespace(values)
                result = func(ns)
                # Sync modified values back to the values dict
                for k in values:
                    if hasattr(result, k):
                        values[k] = getattr(result, k)
                return values

            v1_wrapper.__name__ = func.__name__  # Manually set function name for debugging
            v1_wrapper.__doc__ = func.__doc__
            return root_validator(skip_on_failure=skip_on_failure, allow_reuse=True)(
                v1_wrapper
            )
        else:
            from pydantic import model_validator

            # v2's model_validator(mode='after') receives self directly
            @functools.wraps(func)
            def v2_wrapper(self):
                return func(self)

            return model_validator(mode=mode)(v2_wrapper)

    return decorator


class BaseJsonAbleModel(CompatibleModel):
    """
    Since model fields include functions and custom-typed objects that cannot be directly JSON-serialized, custom JSON serialization is needed.
    """

    def get_str_dict(self):
        model_dict: dict = self.to_dict()  # noqa
        model_dict_copy = OrderedDict()
        for k, v in model_dict.items():
            if isinstance(v, typing.Callable):
                model_dict_copy[k] = str(v)
            # elif k in ['specify_concurrent_pool', 'specify_async_loop'] and v is not None:
            elif (
                type(v).__module__ != "builtins"
            ):  # Custom type objects are not JSON-serializable and need conversion.
                model_dict_copy[k] = str(v)
            else:
                model_dict_copy[k] = v
        return model_dict_copy

    def json_str_value(self):
        try:
            return json.dumps(
                dict(self.get_str_dict()),
                ensure_ascii=False,
            )
        except TypeError as e:
            return str(self.get_str_dict())

    def json_pre(self):
        try:
            return json.dumps(self.get_str_dict(), ensure_ascii=False, indent=4)
        except TypeError as e:
            return str(self.get_str_dict())

    def update_from_dict(self, dictx: dict):
        for k, v in dictx.items():
            setattr(self, k, v)
        return self

    def update_from_kwargs(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        return self

    def update_from_model(self, modelx: BaseModel):
        for k, v in modelx.to_dict().items():
            setattr(self, k, v)
        return self

    @staticmethod
    def init_by_another_model(model_type: typing.Type[BaseModel], modelx: BaseModel):
        init_dict = {}
        for k, v in modelx.to_dict().items():
            if k in model_type.__fields__.keys():
                init_dict[k] = v
        return model_type(**init_dict)


# Cache non-serializable fields per model type
_model_non_serializable_fields_cache: typing.Dict[typing.Type, typing.Set[str]] = {}

def get_cant_json_serializable_fields(model_type: typing.Type[BaseModel]) -> typing.Set[str]:
    """
    Get the list of all field names in a Pydantic model that are not JSON-serializable.
    Uses a cache; each model type is only computed on the first call.

    Args:
        model_type: Pydantic model type

    Returns:
        Set of field names that are not JSON-serializable

    Example:
        >>> from funboost.core.func_params_model import BoosterParams
        >>> fields = get_cant_json_serializable_fields(BoosterParams)
        >>> 'specify_concurrent_pool' in fields
        True
        >>> 'queue_name' in fields
        False
    """
    # If cache exists, return directly
    if model_type in _model_non_serializable_fields_cache:
        return _model_non_serializable_fields_cache[model_type]
    
    import inspect
    from collections.abc import Callable as AbcCallable
    
    non_serializable_fields = set()
    
    # Get all field type annotations for the model
    # Compatible with pydantic v1 and v2
    if hasattr(model_type, 'model_fields'):
        # pydantic v2
        fields_info = model_type.model_fields
    else:
        # pydantic v1
        fields_info = model_type.__fields__

    for field_name, field_info in fields_info.items():
        # Get the type annotation for the field
        if hasattr(field_info, 'annotation'):
            # pydantic v2
            field_type = field_info.annotation
        else:
            # pydantic v1
            field_type = field_info.outer_type_ if hasattr(field_info, 'outer_type_') else field_info.type_

        # Determine if the type is not JSON-serializable
        # Use typing.get_origin and get_args for accurate type checking
        origin = typing.get_origin(field_type)

        # Handle Optional[X] / Union[X, None] types, get the actual type
        if origin is typing.Union:
            args = typing.get_args(field_type)
            # Filter out NoneType to get the actual type
            non_none_types = [arg for arg in args if arg is not type(None)]
            if non_none_types:
                field_type = non_none_types[0]
                origin = typing.get_origin(field_type)

        # Determine if the type is non-serializable:
        # 1. typing.Callable - function types
        # 2. typing.Type - class types
        # 3. Custom class - actual class objects (non-primitive types)
        is_callable = origin is AbcCallable or (hasattr(typing, 'Callable') and origin is getattr(typing, 'Callable', None))
        is_type = origin is type or str(field_type).startswith('typing.Type')

        # Check if it's a custom class:
        # - Must be an actual class (inspect.isclass is True)
        # - Not a primitive type (str, int, float, bool, list, dict)
        # - Not a typing module generic (Literal, Union, Optional etc. are already handled via origin)
        is_custom_class = False
        if not is_callable and not is_type and origin is None:
            # origin is None means it's not a generic type, might be a plain class
            # Check if it's an actual custom class
            if inspect.isclass(field_type):
                # It's a class, check if it's a primitive type
                if field_type not in (str, int, float, bool, list, dict):
                    is_custom_class = True

        if is_callable or is_type or is_custom_class:
            non_serializable_fields.add(field_name)

    # Cache the result
    _model_non_serializable_fields_cache[model_type] = non_serializable_fields
    return non_serializable_fields

if __name__ == '__main__':
    from funboost.core.func_params_model import BoosterParams
    print(get_cant_json_serializable_fields(BoosterParams))