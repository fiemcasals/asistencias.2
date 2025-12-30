from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

def requiere_nivel(min_nivel):
    def decorator(view):
        @login_required
        def _wrapped(request, *args, **kwargs):
            if request.user.nivel >= min_nivel:
                return view(request, *args, **kwargs)
            # En lugar de error 403, redirigimos con mensaje
            messages.error(request, "No tienes permisos para acceder a esa sección.")
            return redirect('asistencias:home')
        return _wrapped
    return decorator
