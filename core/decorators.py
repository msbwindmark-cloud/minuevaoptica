from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from functools import wraps


def gestor_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        perfil = getattr(request, "perfil", None)
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        if perfil is not None and perfil.es_gestor:
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return _wrapped
