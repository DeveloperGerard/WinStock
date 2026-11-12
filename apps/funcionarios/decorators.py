from django.core.exceptions import PermissionDenied

def rol_requerido(*roles_permitidos):
    # creamos una funcion que recibe varios roles 
    def decorator(view_func):
        #aqui recibimos la funcion a decorar

        def wrapper(request, *args, **kwargs):
            #wrapper nos permite evaluar permisos antes de ejecutar
            if not request.user.is_authenticated:
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(request.get_full_path())
            #Como un usuario tiene asociado un rol mediante la foreing puedes acceder a campos de la tabla rol como Admin, Func
            if request.user.rol is None or request.user.rol.nombre not in roles_permitidos:
                raise PermissionDenied

            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator