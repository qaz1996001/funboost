
import functools
import abc
import sys
import typing


class Undefind:
    pass

F = typing.TypeVar('F')
class BaseDecorator(metaclass=abc.ABCMeta):
    """
    Simplifies decorator writing.

    User decorators need to inherit this. Users can redefine the before, after, when_exception methods as needed.

    For consistency and convenience, all decorators must have parameters — user decorators must always include parentheses.

    Users can choose to override the three methods: before, after, when_exception
    """

    # def __init__(self, *args, **kwargs):
    #     pass

    raw_fun = Undefind()
    raw_result = Undefind()
    exc_info = Undefind()
    final_result = Undefind()  # Users can define the value of final_result themselves. If defined, this value is used as the function result; otherwise the raw function result is used.

    def __call__(self, fun:F, *args, **kwargs)->F:
        # print(locals())
        if not callable(fun) or args or kwargs:  # Normally there is only one parameter fun, unless the decorator was used without parentheses.
            raise ValueError('For simplicity and consistency, all decorators use parameterized form. Do not forget to add parentheses after the decorator on the decorated function')
        self.raw_fun = fun
        f = functools.partial(BaseDecorator._execute, self)  # Better for auto-completion than self.execute
        functools.update_wrapper(f, fun, )
        functools.wraps(fun)(f)
        return f

    def _execute(self, *args, **kwargs):
        self.before()
        try:
            self.raw_result = self.raw_fun(*args, **kwargs)
            self.after()
        except Exception as e:
            self.exc_info = sys.exc_info()
            self.when_exception()
        if not isinstance(self.final_result, Undefind):  # Users can define final_result themselves; if defined it becomes the function result.
            return self.final_result
        else:
            return self.raw_result

    def before(self):
        pass

    def after(self):
        pass

    def when_exception(self):
        # print(self.exc_info) # (<class 'ZeroDivisionError'>, ZeroDivisionError('division by zero',), <traceback object at 0x000001D22BA3FD48>)
        raise self.exc_info[1]


if __name__ == '__main__':
    import nb_log  # noqa


    class MyDeco(BaseDecorator):
        def __init__(self, a=5, b=6):
            self.a = a
            self.b = b

        def before(self):
            print('Starting execution')

        # noinspection PyAttributeOutsideInit
        def after(self):
            self.final_result = self.a * self.b * self.raw_result


    def common_deco(a=5, b=6):
        """  The above logic written in the conventional way"""

        def _inner(f):
            @functools.wraps(f)
            def __inner(*args, **kwargs):
                try:
                    print('Starting execution')
                    result = f(*args, **kwargs)
                    return a * b * result
                except Exception as e:
                    raise e

            return __inner

        return _inner


    @MyDeco(b=4)
    # @common_deco(b=4)  # These two decorators are equivalent; choose one.
    def fun3(x):
        print(x)
        return x * 2


    print(type(fun3))
    print(fun3)
    print(fun3.__wrapped__)  # noqa
    print(fun3(10))
