"""Décorateurs et mixins pour le contrôle d'accès basé sur les rôles."""
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(*roles):
    """Restreint l'accès à une vue à certains rôles."""

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            if request.user.role not in roles and not request.user.is_superuser:
                raise PermissionDenied("Accès réservé.")
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


class RoleRequiredMixin:
    """Mixin pour les CBV : roles autorisés via attribut `allowed_roles`."""

    allowed_roles: tuple = ()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.shortcuts import redirect
            return redirect("accounts:login")
        if (
            request.user.role not in self.allowed_roles
            and not request.user.is_superuser
        ):
            raise PermissionDenied("Accès réservé.")
        return super().dispatch(request, *args, **kwargs)


class AgentRequiredMixin(RoleRequiredMixin):
    allowed_roles = ("AGENT", "ADMIN")


class ClientRequiredMixin(RoleRequiredMixin):
    allowed_roles = ("CLIENT",)


class AdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = ("ADMIN",)
