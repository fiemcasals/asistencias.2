from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

@login_required
def switch_role(request, role_id):
    """
    Allows a Supervisor (Level 7) to switch their effective role.
    """
    # Check if the REAL user is a Supervisor (ignore the impersonated role for permission check)
    # We need to check the DB user, but request.user might be modified by middleware.
    # However, the middleware modifies the INSTANCE on the request.
    # We can check the original level if we stored it, or just re-fetch if needed.
    # But simpler: The middleware only lowers the level. If request.user.nivel is 7, they are definitely a supervisor.
    # If they are impersonating (e.g. level 1), request.user.nivel is 1.
    # So we need a way to know if they are ACTUALLY a supervisor.
    
    # Strategy: The middleware should probably attach an 'is_impersonating' or 'original_user' attribute?
    # Or we can just check the DB.
    
    # Re-fetch user from DB to get true level
    from django.contrib.auth import get_user_model
    User = get_user_model()
    real_user = User.objects.get(pk=request.user.pk)
    
    if real_user.nivel != 7:
        return HttpResponseForbidden("Solo supervisores pueden cambiar de rol.")
        
    if role_id not in [1, 2, 3, 6, 7]: # Allowed roles to switch to
         messages.error(request, "Rol inválido.")
         return redirect(request.META.get('HTTP_REFERER', '/'))

    # Set session variable
    request.session['impersonate_role'] = role_id
    
    # Get role name for message
    role_names = dict(User.NIVEL_CHOICES)
    role_name = role_names.get(role_id, "Desconocido")
    
    messages.success(request, f"Rol cambiado a: {role_name}")
    return redirect('/')
