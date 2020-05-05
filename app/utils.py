# -*- coding: utf-8 -*-

from typing import Callable, Any
from flask import abort
from flask_login import current_user
from functools import wraps


def admin_required(func: Callable) -> Callable:
    @wraps(func)
    def decorated_view(*args, **kwargs) -> Any:
        if not current_user.is_admin:
            abort(404)
        return func(*args, **kwargs)

    return decorated_view


def user_required(func: Callable) -> Callable:
    @wraps(func)
    def decorated_view(*args, **kwargs) -> Any:
        if current_user.is_admin:
            abort(404)
        return func(*args, **kwargs)

    return decorated_view
