import threading

_thread_locals = threading.local()


def set_current_account(account):
    _thread_locals.account = account


def get_current_account():
    return getattr(_thread_locals, "account", None)
