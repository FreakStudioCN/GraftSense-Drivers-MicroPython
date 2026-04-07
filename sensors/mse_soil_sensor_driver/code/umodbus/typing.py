# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/3 下午5:25
# @Author  : Developer
# @File    : typing.py
# @Description : 适配MicroPython的typing模块伪实现，解决类型注解缺失报错
# @License : MIT
__version__ = "0.1.0"
__author__ = "Developer"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class _Subscriptable():
    """
    伪实现可下标访问类型，用于兼容泛型注解语法
    Attributes:
        无
    Methods:
        __getitem__(item): 伪实现下标访问
    Notes:
        内部辅助类，无实际运行逻辑

    ==========================================
    Fake subscriptable type for generic annotation compatibility
    Attributes:
        None
    Methods:
        __getitem__(item): Fake subscript access
    Notes:
        Internal helper class, no actual logic
    """
    def __getitem__(self, item: Any) -> None:
        """
        伪实现下标访问运算符
        Args:
            item: 下标参数
        Returns:
            None
        Notes:
            无实际功能，仅兼容语法

        ==========================================
        Fake subscript access operator
        Args:
            item: Subscript parameter
        Returns:
            None
        Notes:
            No actual function, only syntax compatibility
        """
        return None

_subscriptable: _Subscriptable = _Subscriptable()

class Any:
    """
    伪实现Any类型注解
    Notes:
        无实际功能，仅兼容语法

    ==========================================
    Fake Any type annotation
    Notes:
        No actual function, only syntax compatibility
    """
    pass

class NoReturn:
    """
    伪实现NoReturn类型注解
    Notes:
        无实际功能，仅兼容语法

    ==========================================
    Fake NoReturn type annotation
    Notes:
        No actual function, only syntax compatibility
    """
    pass

class ClassVar:
    """
    伪实现ClassVar类型注解
    Notes:
        无实际功能，仅兼容语法

    ==========================================
    Fake ClassVar type annotation
    Notes:
        No actual function, only syntax compatibility
    """
    pass

Union: _Subscriptable = _subscriptable
Optional: _Subscriptable = _subscriptable

class Generic:
    """
    伪实现Generic泛型基类
    Notes:
        无实际功能，仅兼容语法

    ==========================================
    Fake Generic base class
    Notes:
        No actual function, only syntax compatibility
    """
    pass

class NamedTuple:
    """
    伪实现NamedTuple类型注解
    Notes:
        无实际功能，仅兼容语法

    ==========================================
    Fake NamedTuple type annotation
    Notes:
        No actual function, only syntax compatibility
    """
    pass

class Hashable:
    """
    伪实现Hashable类型注解
    Notes:
        无实际功能，仅兼容语法

    ==========================================
    Fake Hashable type annotation
    Notes:
        No actual function, only syntax compatibility
    """
    pass

class Awaitable:
    """
    伪实现Awaitable类型注解
    Notes:
        无实际功能，仅兼容语法

    ==========================================
    Fake Awaitable type annotation
    Notes:
        No actual function, only syntax compatibility
    """
    pass

class Coroutine:
    """
    伪实现Coroutine类型注解
    Notes:
        无实际功能，仅兼容语法

    ==========================================
    Fake Coroutine type annotation
    Notes:
        No actual function, only syntax compatibility
    """
    pass

class AsyncIterable:
    """
    伪实现AsyncIterable类型注解
    Notes:
        无实际功能，仅兼容语法

    ==========================================
    Fake AsyncIterable type annotation
    Notes:
        No actual function, only syntax compatibility
    """
    pass

class AsyncIterator:
    """
    伪实现AsyncIterator类型注解
    Notes:
        无实际功能，仅兼容语法

    ==========================================
    Fake AsyncIterator type annotation
    Notes:
        No actual function, only syntax compatibility
    """
    pass

class Iterable:
    """
    伪实现Iterable类型注解
    Notes:
        无实际功能，仅兼容语法

    ==========================================
    Fake Iterable type annotation
    Notes:
        No actual function, only syntax compatibility
    """
    pass

class Iterator:
    """
    伪实现Iterator类型注解
    Notes:
        无实际功能，仅兼容语法

    ==========================================
    Fake Iterator type annotation
    Notes:
        No actual function, only syntax compatibility
    """
    pass

class Reversible:
    """
    伪实现Reversible类型注解
    Notes:
        无实际功能，仅兼容语法

    ==========================================
    Fake Reversible type annotation
    Notes:
        No actual function, only syntax compatibility
    """
    pass

class Sized:
    """
    伪实现Sized类型注解
    Notes:
        无实际功能，仅兼容语法

    ==========================================
    Fake Sized type annotation
    Notes:
        No actual function, only syntax compatibility
    """
    pass

class Container:
    """
    伪实现Container类型注解
    Notes:
        无实际功能，仅兼容语法

    ==========================================
    Fake Container type annotation
    Notes:
        No actual function, only syntax compatibility
    """
    pass

class Collection:
    """
    伪实现Collection类型注解
    Notes:
        无实际功能，仅兼容语法

    ==========================================
    Fake Collection type annotation
    Notes:
        No actual function, only syntax compatibility
    """
    pass

Callable: _Subscriptable = _subscriptable

class AbstractSet:
    """
    伪实现AbstractSet类型注解
    Notes:
        无实际功能，仅兼容语法

    ==========================================
    Fake AbstractSet type annotation
    Notes:
        No actual function, only syntax compatibility
    """
    pass

class MutableSet:
    """
    伪实现MutableSet类型注解
    Notes:
        无实际功能，仅兼容语法

    ==========================================
    Fake MutableSet type annotation
    Notes:
        No actual function, only syntax compatibility
    """
    pass

class Mapping:
    """
    伪实现Mapping类型注解
    Notes:
        无实际功能，仅兼容语法

    ==========================================
    Fake Mapping type annotation
    Notes:
        No actual function, only syntax compatibility
    """
    pass

class MutableMapping:
    """
    伪实现MutableMapping类型注解
    Notes:
        无实际功能，仅兼容语法

    ==========================================
    Fake MutableMapping type annotation
    Notes:
        No actual function, only syntax compatibility
    """
    pass

class Sequence:
    """
    伪实现Sequence类型注解
    Notes:
        无实际功能，仅兼容语法

    ==========================================
    Fake Sequence type annotation
    Notes:
        No actual function, only syntax compatibility
    """
    pass

class MutableSequence:
    """
    伪实现MutableSequence类型注解
    Notes:
        无实际功能，仅兼容语法

    ==========================================
    Fake MutableSequence type annotation
    Notes:
        No actual function, only syntax compatibility
    """
    pass

class ByteString:
    """
    伪实现ByteString类型注解
    Notes:
        无实际功能，仅兼容语法

    ==========================================
    Fake ByteString type annotation
    Notes:
        No actual function, only syntax compatibility
    """
    pass

Tuple: _Subscriptable = _subscriptable
List: _Subscriptable = _subscriptable

class Deque:
    """
    伪实现Deque类型注解
    Notes:
        无实际功能，仅兼容语法

    ==========================================
    Fake Deque type annotation
    Notes:
        No actual function, only syntax compatibility
    """
    pass

class Set:
    """
    伪实现Set类型注解
    Notes:
        无实际功能，仅兼容语法

    ==========================================
    Fake Set type annotation
    Notes:
        No actual function, only syntax compatibility
    """
    pass

class dict_keys:
    """
    伪实现dict_keys类型注解
    Notes:
        无实际功能，仅兼容语法

    ==========================================
    Fake dict_keys type annotation
    Notes:
        No actual function, only syntax compatibility
    """
    pass

class FrozenSet:
    """
    伪实现FrozenSet类型注解
    Notes:
        无实际功能，仅兼容语法

    ==========================================
    Fake FrozenSet type annotation
    Notes:
        No actual function, only syntax compatibility
    """
    pass

class MappingView:
    """
    伪实现MappingView类型注解
    Notes:
        无实际功能，仅兼容语法

    ==========================================
    Fake MappingView type annotation
    Notes:
        No actual function, only syntax compatibility
    """
    pass

class KeysView:
    """
    伪实现KeysView类型注解
    Notes:
        无实际功能，仅兼容语法

    ==========================================
    Fake KeysView type annotation
    Notes:
        No actual function, only syntax compatibility
    """
    pass

class ItemsView:
    """
    伪实现ItemsView类型注解
    Notes:
        无实际功能，仅兼容语法

    ==========================================
    Fake ItemsView type annotation
    Notes:
        No actual function, only syntax compatibility
    """
    pass

class ValuesView:
    """
    伪实现ValuesView类型注解
    Notes:
        无实际功能，仅兼容语法

    ==========================================
    Fake ValuesView type annotation
    Notes:
        No actual function, only syntax compatibility
    """
    pass

class ContextManager:
    """
    伪实现ContextManager类型注解
    Notes:
        无实际功能，仅兼容语法

    ==========================================
    Fake ContextManager type annotation
    Notes:
        No actual function, only syntax compatibility
    """
    pass

class AsyncContextManager:
    """
    伪实现AsyncContextManager类型注解
    Notes:
        无实际功能，仅兼容语法

    ==========================================
    Fake AsyncContextManager type annotation
    Notes:
        No actual function, only syntax compatibility
    """
    pass

Dict: _Subscriptable = _subscriptable

class DefaultDict:
    """
    伪实现DefaultDict类型注解
    Notes:
        无实际功能，仅兼容语法

    ==========================================
    Fake DefaultDict type annotation
    Notes:
        No actual function, only syntax compatibility
    """
    pass

class Counter:
    """
    伪实现Counter类型注解
    Notes:
        无实际功能，仅兼容语法

    ==========================================
    Fake Counter type annotation
    Notes:
        No actual function, only syntax compatibility
    """
    pass

class ChainMap:
    """
    伪实现ChainMap类型注解
    Notes:
        无实际功能，仅兼容语法

    ==========================================
    Fake ChainMap type annotation
    Notes:
        No actual function, only syntax compatibility
    """
    pass

class Generator:
    """
    伪实现Generator类型注解
    Notes:
        无实际功能，仅兼容语法

    ==========================================
    Fake Generator type annotation
    Notes:
        No actual function, only syntax compatibility
    """
    pass

class AsyncGenerator:
    """
    伪实现AsyncGenerator类型注解
    Notes:
        无实际功能，仅兼容语法

    ==========================================
    Fake AsyncGenerator type annotation
    Notes:
        No actual function, only syntax compatibility
    """
    pass

class Type:
    """
    伪实现Type类型注解
    Notes:
        无实际功能，仅兼容语法

    ==========================================
    Fake Type type annotation
    Notes:
        No actual function, only syntax compatibility
    """
    pass

def cast(typ: Any, val: Any) -> Any:
    """
    伪实现类型转换函数
    Args:
        typ: 目标类型
        val: 待转换值
    Returns:
        原值
    Notes:
        无实际转换逻辑，仅兼容语法

    ==========================================
    Fake type cast function
    Args:
        typ: Target type
        val: Value to cast
    Returns:
        Original value
    Notes:
        No actual cast logic, only syntax compatibility
    """
    return val

def _overload_dummy(*args: Any, **kwds: Any) -> None:
    """
    重载装饰器辅助函数，禁止直接调用
    Raises:
        NotImplementedError: 直接调用时抛出
    Notes:
        内部辅助函数

    ==========================================
    Helper for overload decorator, call forbidden
    Raises:
        NotImplementedError: Raised on direct call
    Notes:
        Internal helper function
    """
    raise NotImplementedError(
        "You should not call an overloaded function. "
        "A series of @overload-decorated functions "
        "outside a stub module should always be followed "
        "by an implementation that is not @overload-ed."
    )

def overload() -> Any:
    """
    伪实现overload装饰器
    Returns:
        辅助函数
    Notes:
        无实际功能，仅兼容语法

    ==========================================
    Fake overload decorator
    Returns:
        Helper function
    Notes:
        No actual function, only syntax compatibility
    """
    return _overload_dummy

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================