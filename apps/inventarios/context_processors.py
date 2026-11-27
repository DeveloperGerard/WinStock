from .acceso import claves_permitidas


def inventarios_permitidos(request):
    return {"inventarios_permitidos": claves_permitidas(request.user)}