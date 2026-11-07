from .models import set_current_org, set_audit_context, _org_context, _audit_context


class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        org = None
        perfil = None
        if getattr(request, "user", None) and request.user.is_authenticated:
            perfil = getattr(request.user, "perfil", None)
            if perfil is not None:
                org = perfil.organizacion
        if org is None:
            # Sitio público de una sola óptica: usar la primera organización disponible
            try:
                from .models import Organizacion
                org = Organizacion.objects.order_by("id").first()
            except Exception:
                org = None
        request.perfil = perfil
        request.organizacion = org
        org_token = set_current_org(org)
        try:
            response = self.get_response(request)
        finally:
            _org_context.reset(org_token)
        return response


def _client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class AuditoriaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ctx = {
            "user": getattr(request, "user", None),
            "ip": _client_ip(request),
            "user_agent": request.META.get("HTTP_USER_AGENT", ""),
            "ruta": request.path,
            "metodo": request.method,
            "organizacion": getattr(request, "organizacion", None),
        }
        token = set_audit_context(ctx)
        try:
            response = self.get_response(request)
        finally:
            _audit_context.reset(token)
        return response
