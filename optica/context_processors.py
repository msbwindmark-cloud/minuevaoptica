from .models import Ajustes


def optica(request):
    org = getattr(request, "organizacion", None)
    ajustes = None
    if org is not None:
        try:
            ajustes = Ajustes.for_org(org)
        except Exception:
            ajustes = None
    return {"ajustes": ajustes}
