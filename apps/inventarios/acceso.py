from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .models import Inventario


def es_admin(user):
    return bool(user.is_authenticated and user.rol and user.rol.nombre == "adm")


def claves_permitidas(user):
    """Set de claves a las que el usuario accede. Se calcula una vez por request."""
    if not user.is_authenticated:
        return set()
    if not hasattr(user, "_claves_inventario"):
        if es_admin(user):
            claves = set(Inventario.objects.values_list("clave", flat=True))
        else:
            claves = set(user.inventarios.values_list("clave", flat=True))
        user._claves_inventario = claves
    return user._claves_inventario


def inventario_requerido(*claves):
    """Exige TODAS las claves indicadas. Sin sesión redirige al login; sin permiso, 403."""
    def decorador(vista):
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            if not set(claves) <= claves_permitidas(request.user):
                raise PermissionDenied("No tienes acceso a este inventario.")
            return vista(request, *args, **kwargs)
        return login_required(envoltura)
    return decorador