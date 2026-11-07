def tenant(request):
    return {
        "organizacion": getattr(request, "organizacion", None),
        "perfil": getattr(request, "perfil", None),
    }
