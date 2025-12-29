from django.utils.functional import SimpleLazyObject

class RoleSwitchMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.user.nivel == 7: # Supervisor
            # Check if there is a role switch in session
            target_role = request.session.get('impersonate_role')
            if target_role:
                # Override the user's nivel for this request only
                # We use a simple assignment because request.user is mutable in the request cycle
                # But we must be careful not to save this user object to DB with the wrong level
                # The view code should just read request.user.nivel
                try:
                    request.user.nivel = int(target_role)
                except (ValueError, TypeError):
                    pass
        
        response = self.get_response(request)
        return response
