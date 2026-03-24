

import typing
import uuid
import datetime
import time
import json

class FunboostException(Exception):
    """
    Enterprise-grade general exception base class.
    Supports subclass default message / code / error_data.
    Automatically generates trace_id (usable for distributed logging).
    """

    # Subclasses can override the following defaults
    default_message = "An error occurred"
    default_code = None
    default_error_data = None
    enable_trace_id = False

    def __init__(self, message=None, code=None, error_data:typing.Optional[dict]=None, trace_id=None):
        # Allow instances to override default fields
        self.message = message or self.default_message
        self.code = code if code is not None else self.default_code
        self.error_data = error_data if error_data is not None else self.default_error_data

        # Auto-generate trace_id
        if trace_id:
            self.trace_id = trace_id
        elif self.enable_trace_id:
            self.trace_id = str(uuid.uuid4())
        else:
            self.trace_id = None

        # super().__init__(self.message)
        super().__init__(message,code, error_data,trace_id)

    # Elegant string representation
    def __str__(self):
        parts = [f"{self.__class__.__name__}"]  # 显示异常类型

        if self.code is not None:
            parts.append(f"[{self.code}]")

        parts.append(self.message)

        if self.error_data:
            parts.append(f"error_data={self.error_data}")

        if self.trace_id:
            parts.append(f"trace_id={self.trace_id}")

        return " | ".join(parts)

    # REPL / logging info
    def __repr__(self):
        parts = [self.__class__.__name__]

        if self.code is not None:
            parts.append(f"code={self.code}")

        parts.append(f"message={self.message!r}")

        if self.trace_id:
            parts.append(f"trace_id={self.trace_id}")

        return f"<{' '.join(parts)}>"

    # JSON serialization
    def to_dict(self):
        # Get current UTC time with timezone
        utc_dt = datetime.datetime.now(datetime.timezone.utc)
        utc_str = utc_dt.isoformat()  # 2025-12-10T08:30:00+00:00

        # Get current local time with local timezone
        local_dt = utc_dt.astimezone()  # Convert to local timezone
        local_str = local_dt.isoformat()  # 2025-12-10T16:30:00+08:00

        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "code": self.code,
            "error_data": self.error_data,
            "trace_id": getattr(self, "trace_id", None),
            "ts": time.time(),
            "utc_time": utc_str,
            "local_time": local_str 
        }

    def to_json(self,pretty=False):
        return json.dumps(self.to_dict(),indent=4 if pretty else None,ensure_ascii=False)

    def to_fastapi_response(self, http_status=200):
        """Return a FastAPI JSONResponse, keeping the exception consistent with FastAPI's interface model for reuse.


        Recommended pydantic model (or use allow_extra):

        ```python
        T = typing.TypeVar('T')

        class BaseResponse(BaseModel, typing.Generic[T]):
            '''
            Unified generic response model

            Field descriptions:
                succ: Whether the request succeeded, True for success, False for failure
                msg: Message description
                data: Returned data, using generic T
                code: Business status code, 200 for success, others for various errors
                error: Error type name (optional), e.g. "QueueNameNotExists", "ValueError"
                traceback: Exception stack trace (optional), only returned on error
                trace_id: Trace ID (optional), for distributed tracing
            '''
            succ: bool
            msg: str
            data: typing.Optional[T] = None
            error_data: typing.Optional[typing.Dict] = None
            code: typing.Optional[int] = 200
            error: typing.Optional[str] = None
            traceback: typing.Optional[str] = None
            trace_id: typing.Optional[str] = None
        ```


        Refer to funboost/faas/fastapi_adapter.py's
        register_funboost_exception_handlers and handle_funboost_exceptions for automatic capture and conversion.
        """


        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=http_status,
            content=self.to_dict()
        )
        # return FuncParamsError().to_fastapi_response()



class ExceptionForRetry(FunboostException):
    """Raise this to trigger a retry. This is just a subclass definition, using it is optional - the framework will auto-retry on any error type"""


class ExceptionForRequeue(FunboostException):
    """When the framework detects this error, the message is put back into the current queue"""

class FunboostWaitRpcResultTimeout(FunboostException):
    """Waiting for RPC result exceeded the specified timeout"""

class FunboostRpcResultError(FunboostException):
    """RPC result is in error status"""

class HasNotAsyncResult(FunboostException):
    pass

class ExceptionForPushToDlxqueue(FunboostException):
    """When the framework detects this error, the message is published to the dead letter queue"""


class BoostDecoParamsIsOldVersion(FunboostException):
    default_message = """
Your @boost parameters use the old style. Please use the new parameter style. The old parameter style no longer supports function parameter auto-completion.

Old version @boost decorator style:
@boost('queue_name_xx',qps=3)
def f(x):
    pass


What users need to change:
@boost(BoosterParams(queue_name='queue_name_xx',qps=3))
def f(x):
    pass

Just wrap the original function parameters with BoosterParams.

Reasons for this change in @boost, the most important funboost core method:
1/ During framework development, Booster and Consumer needed to repeatedly declare parameters in multiple places.
2/ Too many parameters needed locals() conversion, which was cumbersome.
    """


class QueueNameNotExists(FunboostException):
    default_message = "queue name not exists"
    default_code = 4001

class FuncParamsError(FunboostException):
    default_message = "consuming function input params error"
    default_code = 5001



if __name__ == '__main__':
    try:
        raise FuncParamsError(
            'testmsg error',
            error_data={'k':'v'},
            trace_id='1234567890',
            
        )
    except FunboostException as e:
        print(e)
        print(str(e))
        print(e.to_json(pretty=True))
