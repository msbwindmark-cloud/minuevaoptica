import json
from datetime import datetime, timedelta

from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.decorators import gestor_required, superuser_required

from .forms import ConsultaForm, CitaForm, ModeloForm, MarcaForm, CategoriaForm, AjustesForm, EntradaForm, RecordatorioForm, PaginaForm
from .models import (
    Ajustes, Marca, Categoria, Modelo, FotoModelo, Consulta, Cita, Entrada, Opinion,
    PushSubscription, RecordatorioRevision, Pagina,
)


def _org(request):
    return request.organizacion


def _ajustes(request):
    org = _org(request)
    if org is None:
        return None
    return Ajustes.for_org(org)


# ---------- Public ----------

def home(request):
    org = _org(request)
    ajustes = _ajustes(request)
    destacados = Modelo.objects.filter(visible=True, destacado=True)[:8]
    novedades = Modelo.objects.filter(visible=True, novedad=True)[:8]
    entradas = Entrada.objects.filter(publicada=True)[:3]
    opiniones = Opinion.objects.filter(visible=True)[:6]
    context = {
        "ajustes": ajustes,
        "destacados": destacados,
        "novedades": novedades,
        "entradas": entradas,
        "opiniones": opiniones,
        "abierto": estado_tienda(ajustes),
    }
    return render(request, "optica/publico/home.html", context)


def estado_tienda(ajustes):
    from django.utils import timezone as djtz
    if not ajustes:
        return {"abierto": True, "texto": "Abierto"}
    if ajustes.cerrado:
        return {"abierto": False, "texto": "Cerrado temporalmente"}
    now = djtz.localtime().timetz().replace(microsecond=0, tzinfo=None)
    ap = ajustes.hora_apertura
    ci = ajustes.hora_cierre
    if ap <= now <= ci:
        return {"abierto": True, "texto": "Abierto hasta las " + ap.strftime("%H:%M") if False else f"Abierto hasta las {ci.strftime('%H:%M')}"}
    if now < ap:
        return {"abierto": False, "texto": f"Abrimos hoy a las {ap.strftime('%H:%M')}"}
    return {"abierto": False, "texto": f"Abrimos manana a las {ap.strftime('%H:%M')}"}


def catalogo(request):
    qs = Modelo.objects.filter(visible=True).select_related("marca", "categoria")
    q = request.GET.get("q", "").strip()
    marca = request.GET.get("marca")
    categoria = request.GET.get("categoria")
    genero = request.GET.get("genero")
    forma = request.GET.get("forma")
    color = request.GET.get("color")
    if q:
        qs = qs.filter(Q(nombre__icontains=q) | Q(marca__nombre__icontains=q) | Q(color__icontains=q))
    if marca:
        qs = qs.filter(marca__slug=marca)
    if categoria:
        qs = qs.filter(categoria__slug=categoria)
    if genero:
        qs = qs.filter(genero=genero)
    if forma:
        qs = qs.filter(forma=forma)
    if color:
        qs = qs.filter(color__icontains=color)
    paginator = Paginator(qs, request.GET.get("page_size", 12))
    try:
        page_size = int(request.GET.get("page_size", 12))
    except ValueError:
        page_size = 12
    page_size = max(5, min(page_size, 48))
    paginator = Paginator(qs, page_size)
    page = paginator.get_page(request.GET.get("page"))
    marcas = Marca.objects.filter(visible=True)
    categorias = Categoria.objects.filter(visible=True)
    context = {
        "page": page,
        "marcas": marcas,
        "categorias": categorias,
        "q": q,
        "filtros": {
            "marca": marca, "categoria": categoria, "genero": genero,
            "forma": forma, "color": color,
        },
        "page_size": page_size,
    }
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = render_to_string("optica/publico/_catalogo_grid.html", context, request=request)
        return JsonResponse({"html": html})
    return render(request, "optica/publico/catalogo.html", context)


def modelo_detail(request, slug):
    modelo = get_object_or_404(Modelo, slug=slug, visible=True)
    modelo.vistas = modelo.vistas + 1
    modelo.save(update_fields=["vistas"])
    relacionados = Modelo.objects.filter(visible=True, categoria=modelo.categoria).exclude(pk=modelo.pk)[:4]
    context = {"modelo": modelo, "relacionados": relacionados}
    return render(request, "optica/publico/modelo_detail.html", context)


def marcas(request):
    return render(request, "optica/publico/marcas.html", {"marcas": Marca.objects.filter(visible=True)})


def marca_detail(request, slug):
    marca = get_object_or_404(Marca, slug=slug, visible=True)
    modelos = Modelo.objects.filter(visible=True, marca=marca)
    return render(request, "optica/publico/marca_detail.html", {"marca": marca, "modelos": modelos})


def encuentra_tu_montura(request):
    return render(request, "optica/publico/encuentra.html")


def recomendar(request):
    # AJAX: recibe respuestas y devuelve modelos recomendados
    if request.method != "POST":
        return JsonResponse({"error": "method"}, status=405)
    data = json.loads(request.body or "{}")
    cara = data.get("cara")
    estilo = data.get("estilo")
    uso = data.get("uso")
    genero = data.get("genero")
    qs = Modelo.objects.filter(visible=True)
    if genero:
        qs = qs.filter(genero__in=[genero, "unisex"])
    # heurística simple
    forma_map = {
        "redonda": ["cuadrada", "rectangular"],
        "cuadrada": ["redonda", "ovalada"],
        "ovalada": ["cuadrada", "cat-eye"],
        "corazon": ["redonda", "cat-eye"],
    }
    if cara in forma_map:
        qs = qs.filter(forma__in=forma_map[cara])
    if estilo == "clasico":
        qs = qs.order_by("-destacado", "-fecha_alta")
    elif estilo == "moderno":
        qs = qs.filter(novedad=True) | qs.filter(forma__in=["cat-eye", "aviador"])
    qs = qs.distinct()[:12]
    items = []
    for m in qs:
        fp = m.foto_portada
        items.append({
            "id": m.id,
            "nombre": str(m),
            "slug": m.slug,
            "url": reverse("optica:modelo_detail", args=[m.slug]),
            "foto": fp.imagen.url if fp else "",
            "precio": m.precio_display,
        })
    return JsonResponse({"items": items})


def favoritos(request):
    return render(request, "optica/publico/favoritos.html")


def comparar(request):
    ids = request.GET.getlist("ids")
    modelos = Modelo.objects.filter(visible=True, id__in=ids)[:3]
    return render(request, "optica/publico/comparar.html", {"modelos": modelos})


def citas(request):
    if request.method == "POST":
        form = CitaForm(request.POST)
        if form.is_valid():
            cita = form.save(commit=False)
            org = _org(request)
            cita.organizacion = org
            cita.save()
            _enviar_correo_cita(org, cita)
            _enviar_push_gestores(org, "Nueva cita solicitada", f"{cita.nombre} - {cita.fecha_hora}")
            return redirect("optica:cita_ok")
    else:
        form = CitaForm()
    return render(request, "optica/publico/citas.html", {"form": form})


def cita_ok(request):
    return render(request, "optica/publico/cita_ok.html")


def novedades(request):
    entradas = Entrada.objects.filter(publicada=True)
    return render(request, "optica/publico/novedades.html", {"entradas": entradas})


def entrada_detail(request, slug):
    entrada = get_object_or_404(Entrada, slug=slug, publicada=True)
    return render(request, "optica/publico/entrada_detail.html", {"entrada": entrada})


def contacto(request):
    org = _org(request)
    ajustes = _ajustes(request)
    if request.method == "POST":
        form = ConsultaForm(request.POST)
        if form.is_valid():
            # rate limit por IP
            ip = _client_ip(request)
            key = f"contacto:{ip}"
            if cache.get(key, 0) >= 5:
                form.add_error(None, "Demasiados envíos. Inténtalo más tarde.")
            else:
                cache.set(key, cache.get(key, 0) + 1, 3600)
                consulta = form.save(commit=False)
                consulta.organizacion = org
                if consulta.consentimiento:
                    consulta.consentimiento_fecha = timezone.now()
                consulta.save()
                _enviar_correo_consulta(org, ajustes, consulta)
                _enviar_push_gestores(org, "Nueva consulta web", f"{consulta.nombre}: {consulta.mensaje[:80]}")
                return redirect("optica:contacto_ok")
    else:
        # modelo preseleccionado
        initial = {}
        if request.GET.get("modelo"):
            initial["modelo"] = request.GET.get("modelo")
        form = ConsultaForm(initial=initial)
    return render(request, "optica/publico/contacto.html", {"form": form, "ajustes": ajustes})


def contacto_ok(request):
    return render(request, "optica/publico/contacto_ok.html")


def nosotros(request):
    org = _org(request)
    pagina = Pagina.objects.filter(organizacion=org, slug="nosotros", publicada=True).first()
    return render(request, "optica/publico/nosotros.html", {"ajustes": _ajustes(request), "pagina": pagina})


def aviso_legal(request):
    org = _org(request)
    pagina = Pagina.objects.filter(organizacion=org, slug="aviso-legal", publicada=True).first()
    return render(request, "optica/publico/legal/aviso_legal.html", {"pagina": pagina})


def privacidad(request):
    org = _org(request)
    pagina = Pagina.objects.filter(organizacion=org, slug="privacidad", publicada=True).first()
    return render(request, "optica/publico/legal/privacidad.html", {"pagina": pagina})


def cookies(request):
    org = _org(request)
    pagina = Pagina.objects.filter(organizacion=org, slug="cookies", publicada=True).first()
    return render(request, "optica/publico/legal/cookies.html", {"pagina": pagina})


def probador(request):
    modelos = Modelo.objects.filter(visible=True)
    return render(request, "optica/publico/probador.html", {"modelos": modelos})


def cita_ics(request, pk):
    org = _org(request)
    cita = get_object_or_404(Cita, pk=pk, organizacion=org)
    from django.http import HttpResponse
    dt = cita.fecha_hora
    dtend = dt + timedelta(hours=1)
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Optica Espartinas//Cita//ES",
        "BEGIN:VEVENT",
        f"UID:cita-{cita.pk}@optica",
        f"DTSTAMP:{dt.strftime('%Y%m%dT%H%M%SZ')}",
        f"DTSTART:{dt.strftime('%Y%m%dT%H%M%SZ')}",
        f"DTEND:{dtend.strftime('%Y%m%dT%H%M%SZ')}",
        f"SUMMARY:Cita optica - {cita.nombre}",
        f"DESCRIPTION:{cita.get_motivo_display()} - {cita.notas}",
        "END:VEVENT",
        "END:VCALENDAR",
    ]
    resp = HttpResponse("\r\n".join(lines), content_type="text/calendar")
    resp["Content-Disposition"] = f'attachment; filename="cita-{cita.pk}.ics"'
    return resp


def recordatorio(request):
    org = _org(request)
    if request.method == "POST":
        form = RecordatorioForm(request.POST)
        if form.is_valid():
            r = form.save(commit=False)
            r.organizacion = org
            r.save()
            return redirect("optica:recordatorio_ok")
    else:
        form = RecordatorioForm()
    return render(request, "optica/publico/recordatorio.html", {"form": form})


def recordatorio_ok(request):
    return render(request, "optica/publico/recordatorio_ok.html")


@gestor_required
def gestion_recordatorios(request):
    org = _org(request)
    items = RecordatorioRevision.objects.filter(organizacion=org)
    return render(request, "optica/gestion/recordatorios.html", {"items": items})


@gestor_required
def gestion_estadisticas(request):
    org = _org(request)
    from django.db.models import Count
    top_vistos = Modelo.objects.filter(organizacion=org).order_by("-vistas")[:5]
    top_guardados = Modelo.objects.filter(organizacion=org).order_by("-guardados")[:5]
    from django.db.models.functions import TruncMonth
    consultas_mes = (
        Consulta.objects.filter(organizacion=org)
        .annotate(m=TruncMonth("fecha"))
        .values("m")
        .annotate(n=Count("id"))
        .order_by("-m")[:6]
    )
    citas_estado = Cita.objects.filter(organizacion=org).values("estado").annotate(n=Count("id"))
    context = {
        "top_vistos": top_vistos,
        "top_guardados": top_guardados,
        "consultas_mes": consultas_mes,
        "citas_estado": citas_estado,
        "total_modelos": Modelo.objects.filter(organizacion=org).count(),
        "total_consultas": Consulta.objects.filter(organizacion=org).count(),
        "total_citas": Cita.objects.filter(organizacion=org).count(),
    }
    return render(request, "optica/gestion/estadisticas.html", context)


@gestor_required
def gestion_kiosco(request):
    org = _org(request)
    destacados = Modelo.objects.filter(organizacion=org, visible=True, destacado=True)
    if not destacados.exists():
        destacados = Modelo.objects.filter(organizacion=org, visible=True)[:8]
    return render(request, "optica/gestion/kiosco.html", {"destacados": destacados})


def pagina(request, slug):
    org = _org(request)
    p = get_object_or_404(Pagina, slug=slug, organizacion=org, publicada=True)
    return render(request, "optica/publico/pagina.html", {"pagina": p})


@gestor_required
def gestion_paginas(request):
    org = _org(request)
    paginas = Pagina.objects.filter(organizacion=org)
    if request.method == "POST":
        form = PaginaForm(request.POST)
        if form.is_valid():
            pg = form.save(commit=False)
            pg.organizacion = org
            pg.save()
            return redirect("optica:gestion_paginas")
    else:
        form = PaginaForm()
    return render(request, "optica/gestion/paginas.html", {"form": form, "paginas": paginas})


@gestor_required
def gestion_pagina_editar(request, pk):
    org = _org(request)
    pg = get_object_or_404(Pagina, pk=pk, organizacion=org)
    if request.method == "POST":
        form = PaginaForm(request.POST, instance=pg)
        if form.is_valid():
            form.save()
            return redirect("optica:gestion_paginas")
    else:
        form = PaginaForm(instance=pg)
    return render(request, "optica/gestion/pagina_form.html", {"form": form, "pagina": pg})


@superuser_required
def gestion_usuarios(request):
    from django.contrib.auth.models import User
    org = _org(request)
    users = User.objects.all().select_related("perfil")
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        email = request.POST.get("email", "")
        rol = request.POST.get("rol", "gestor")
        org_id = request.POST.get("organizacion")
        if username and password:
            u = User.objects.create_user(username=username, password=password, email=email)
            from core.models import Organizacion, Perfil
            o = Organizacion.objects.filter(pk=org_id).first() or org
            Perfil.objects.create(user=u, organizacion=o, rol=rol)
            return redirect("optica:gestion_usuarios")
    from core.models import Organizacion
    orgs = Organizacion.objects.all()
    return render(request, "optica/gestion/usuarios.html", {"users": users, "orgs": orgs})


@gestor_required
def gestion_2fa(request):
    from django.contrib.auth import login, get_user_model
    import pyotp
    uid = request.session.get("pending_2fa_user")
    if not uid:
        return redirect("optica:gestion_login")
    User = get_user_model()
    user = User.objects.get(pk=uid)
    error = None
    if request.method == "POST":
        code = request.POST.get("code", "").strip()
        secret = user.perfil.totp_secret
        if pyotp.TOTP(secret).verify(code, valid_window=1):
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            if request.session.get("remember_me"):
                request.session.set_expiry(60 * 60 * 24 * 30)
            else:
                request.session.set_expiry(0)
            request.session.pop("pending_2fa_user", None)
            request.session.pop("remember_me", None)
            return redirect("optica:gestion_dashboard")
        error = "Código incorrecto."
    return render(request, "optica/gestion/2fa.html", {"error": error})


@gestor_required
def gestion_2fa_setup(request):
    from django.contrib.auth import get_user_model
    import pyotp, qrcode
    from io import BytesIO
    from django.http import HttpResponse
    user = request.user
    perfil = user.perfil
    if not perfil.totp_secret:
        perfil.totp_secret = pyotp.random_base32()
        perfil.save(update_fields=["totp_secret"])
    secret = perfil.totp_secret
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=user.username, issuer_name="Óptica Espartinas")
    img = qrcode.make(uri)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    if request.GET.get("qr"):
        return HttpResponse(buf.getvalue(), content_type="image/png")
    return render(request, "optica/gestion/2fa_setup.html", {"secret": secret})


def manifest(request):
    from django.http import HttpResponse
    import os
    from django.conf import settings
    path = os.path.join(settings.BASE_DIR, "static", "manifest.webmanifest")
    with open(path, "rb") as f:
        return HttpResponse(f.read(), content_type="application/manifest+json")


def health(request):
    from django.http import JsonResponse
    return JsonResponse({"status": "ok"})


@login_required
def manual_pdf(request):
    from django.http import FileResponse, Http404
    import os
    from django.conf import settings
    if not (request.user.is_superuser or (hasattr(request.user, "perfil") and request.user.perfil.es_gestor)):
        raise Http404
    path = os.path.join(settings.BASE_DIR, "static", "manual_usuario.pdf")
    if not os.path.exists(path):
        raise Http404
    return FileResponse(open(path, "rb"), content_type="application/pdf")


def robots_txt(request):
    from django.http import HttpResponse
    content = "User-agent: *\nAllow: /\nSitemap: /sitemap.xml\n"
    return HttpResponse(content, content_type="text/plain")


def service_worker(request):
    from django.http import HttpResponse
    from django.conf import settings
    import os
    path = os.path.join(settings.BASE_DIR, "static", "sw.js")
    with open(path, "rb") as f:
        resp = HttpResponse(f.read(), content_type="application/javascript")
    resp["Service-Worker-Allowed"] = "/"
    return resp


def push_clave(request):
    from django.conf import settings
    return JsonResponse({"publicKey": getattr(settings, "VAPID_PUBLIC_KEY", "")})


@require_POST
def push_suscribir(request):
    import json
    try:
        data = json.loads(request.body or "{}")
    except Exception:
        data = {}
    endpoint = data.get("endpoint")
    keys = data.get("keys") or {}
    user = request.user if request.user.is_authenticated else None
    org = request.organizacion
    if not user or not endpoint or org is None:
        return JsonResponse({"ok": False}, status=400)
    PushSubscription.objects.update_or_create(
        endpoint=endpoint,
        defaults={"organizacion": org, "user": user, "p256dh": keys.get("p256dh", ""), "auth": keys.get("auth", "")},
    )
    return JsonResponse({"ok": True})


@require_POST
def push_baja(request):
    import json
    try:
        data = json.loads(request.body or "{}")
    except Exception:
        data = {}
    endpoint = data.get("endpoint")
    if endpoint:
        PushSubscription.objects.filter(endpoint=endpoint).delete()
    return JsonResponse({"ok": True})


@require_POST
def push_probar(request):
    from django.contrib.auth.models import User
    from .utils import enviar_push
    subs = PushSubscription.objects.filter(user=request.user)
    enviados = enviar_push(subs, "Aviso de prueba", "Las notificaciones de la óptica funcionan.")
    return JsonResponse({"ok": True, "enviados": enviados})


def _enviar_push_gestores(org, titulo, cuerpo, exclude_user=None):
    from django.contrib.auth.models import User
    from .utils import enviar_push
    users = User.objects.filter(perfil__organizacion=org, perfil__rol="gestor")
    subs = PushSubscription.objects.filter(user__in=users)
    if exclude_user is not None:
        subs = subs.exclude(user=exclude_user)
    return enviar_push(subs, titulo, cuerpo)


def _client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _enviar_correo_consulta(org, ajustes, consulta):
    from django.core.mail import send_mail
    from django.conf import settings
    try:
        modelo_txt = str(consulta.modelo) if consulta.modelo else "—"
        cuerpo = f"""Nueva consulta desde la web

Nombre: {consulta.nombre}
Teléfono: {consulta.telefono}
Email: {consulta.email or '—'}
Modelo: {modelo_txt}

Mensaje:
{consulta.mensaje}
"""
        send_mail(
            subject=f"Nueva consulta web - {consulta.nombre}",
            message=cuerpo,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[ajustes.email] if ajustes and ajustes.email else ([settings.DEFAULT_FROM_EMAIL]),
            fail_silently=True,
        )
        # acuse al cliente
        if consulta.email:
            send_mail(
                subject="Hemos recibido tu mensaje",
                message="Gracias por contactar con nosotros. Te responderemos en breve.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[consulta.email],
                fail_silently=True,
            )
    except Exception:
        pass


def _enviar_correo_cita(org, cita):
    from django.core.mail import send_mail
    from django.conf import settings
    ajustes = Ajustes.for_org(org) if org else None
    try:
        send_mail(
            subject=f"Nueva cita solicitada - {cita.nombre}",
            message=f"{cita.nombre} solicita cita el {cita.fecha_hora} ({cita.get_motivo_display()}). Tel: {cita.telefono}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[ajustes.email] if ajustes and ajustes.email else [settings.DEFAULT_FROM_EMAIL],
            fail_silently=True,
        )
    except Exception:
        pass


# ---------- Gestión ----------

def gestion_login(request):
    from django.contrib.auth import authenticate, login
    error = None
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if not (user.is_superuser or getattr(user, "perfil", None) and user.perfil.es_gestor):
                error = "No tienes acceso a la gestión."
            else:
                perfil = getattr(user, "perfil", None)
                if perfil is not None and perfil.totp_secret:
                    request.session["pending_2fa_user"] = user.pk
                    request.session["remember_me"] = bool(request.POST.get("remember"))
                    return redirect("optica:gestion_2fa")
                login(request, user, backend="django.contrib.auth.backends.ModelBackend")
                if request.POST.get("remember"):
                    request.session.set_expiry(60 * 60 * 24 * 30)
                else:
                    request.session.set_expiry(0)
                return redirect("optica:gestion_dashboard")
        else:
            error = "Usuario o contraseña incorrectos."
    return render(request, "optica/gestion/login.html", {"error": error})


def gestion_logout(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect("/")


@gestor_required
def gestion_dashboard(request):
    org = _org(request)
    modelos = Modelo.objects.filter(organizacion=org)
    consultas_sin_leer = Consulta.objects.filter(organizacion=org, leida=False).count()
    citas_pendientes = Cita.objects.filter(organizacion=org, estado="pendiente").count()
    context = {
        "modelos_count": modelos.count(),
        "visibles": modelos.filter(visible=True).count(),
        "consultas_sin_leer": consultas_sin_leer,
        "citas_pendientes": citas_pendientes,
        "ultimas_consultas": Consulta.objects.filter(organizacion=org)[:5],
        "ultimas_citas": Cita.objects.filter(organizacion=org)[:5],
    }
    return render(request, "optica/gestion/dashboard.html", context)


@gestor_required
def gestion_modelos(request):
    org = _org(request)
    q = request.GET.get("q", "").strip()
    qs = Modelo.objects.filter(organizacion=org).select_related("marca", "categoria")
    if q:
        qs = qs.filter(Q(nombre__icontains=q) | Q(marca__nombre__icontains=q))
    paginator = Paginator(qs, 10)
    page = paginator.get_page(request.GET.get("page"))
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = render_to_string("optica/gestion/_modelos_rows.html", {"page": page}, request=request)
        return JsonResponse({"html": html})
    return render(request, "optica/gestion/modelos_list.html", {"page": page, "q": q})


@gestor_required
def gestion_modelo_crear(request):
    org = _org(request)
    if request.method == "POST":
        form = ModeloForm(request.POST, organizacion=org)
        if form.is_valid():
            m = form.save(commit=False)
            m.organizacion = org
            m.save()
            return redirect("optica:gestion_modelos")
    else:
        form = ModeloForm(organizacion=org)
    return render(request, "optica/gestion/modelo_form.html", {"form": form, "titulo": "Nueva gafa"})


@gestor_required
def gestion_modelo_editar(request, pk):
    org = _org(request)
    modelo = get_object_or_404(Modelo, pk=pk, organizacion=org)
    if request.method == "POST":
        form = ModeloForm(request.POST, instance=modelo, organizacion=org)
        if form.is_valid():
            form.save()
            return redirect("optica:gestion_modelos")
    else:
        form = ModeloForm(instance=modelo, organizacion=org)
    return render(request, "optica/gestion/modelo_form.html", {"form": form, "titulo": "Editar gafa", "modelo": modelo})


@gestor_required
def gestion_modelo_rapido(request):
    org = _org(request)
    marcas = Marca.objects.filter(organizacion=org)
    categorias = Categoria.objects.filter(organizacion=org)
    if request.method == "POST":
        marca = get_object_or_404(Marca, pk=request.POST.get("marca"), organizacion=org)
        categoria = get_object_or_404(Categoria, pk=request.POST.get("categoria"), organizacion=org)
        nombre = request.POST.get("nombre", "").strip() or "Nueva gafa"
        m = Modelo.objects.create(
            organizacion=org, marca=marca, categoria=categoria, nombre=nombre,
            descripcion_corta=request.POST.get("descripcion_corta", ""),
            visible=True,
        )
        if request.FILES.get("foto"):
            FotoModelo.objects.create(modelo=m, imagen=request.FILES["foto"], organizacion=org)
        return redirect("optica:gestion_modelo_editar", pk=m.pk)
    return render(request, "optica/gestion/modelo_rapido.html", {"marcas": marcas, "categorias": categorias})


@gestor_required
def gestion_modelo_duplicar(request, pk):
    org = _org(request)
    original = get_object_or_404(Modelo, pk=pk, organizacion=org)
    nuevo = Modelo.objects.create(
        organizacion=org, marca=original.marca, categoria=original.categoria,
        nombre=original.nombre + " (copia)", descripcion_corta=original.descripcion_corta,
        descripcion_larga=original.descripcion_larga, precio=original.precio,
        precio_texto=original.precio_texto, material=original.material, forma=original.forma,
        ancho_lente=original.ancho_lente, puente=original.puente, varilla=original.varilla,
        color=original.color, genero=original.genero, destacado=original.destacado,
        novedad=original.novedad, visible=False,
    )
    for f in original.fotos.all():
        FotoModelo.objects.create(modelo=nuevo, imagen=f.imagen, alt=f.alt, organizacion=org)
    return redirect("optica:gestion_modelo_editar", pk=nuevo.pk)


@gestor_required
@require_POST
def gestion_modelo_borrar(request, pk):
    org = _org(request)
    modelo = get_object_or_404(Modelo, pk=pk, organizacion=org)
    modelo.delete()
    return redirect("optica:gestion_modelos")


@gestor_required
@require_POST
def gestion_modelo_toggle(request, pk):
    org = _org(request)
    modelo = get_object_or_404(Modelo, pk=pk, organizacion=org)
    field = request.POST.get("field")
    if field in ("visible", "destacado", "novedad"):
        setattr(modelo, field, not getattr(modelo, field))
        modelo.save(update_fields=[field])
    return JsonResponse({"ok": True, "value": getattr(modelo, field)})


@gestor_required
def gestion_fotos(request, pk):
    org = _org(request)
    modelo = get_object_or_404(Modelo, pk=pk, organizacion=org)
    if request.method == "POST" and request.FILES.get("imagen"):
        FotoModelo.objects.create(modelo=modelo, imagen=request.FILES["imagen"], organizacion=org)
    fotos = modelo.fotos.all()
    return render(request, "optica/gestion/fotos.html", {"modelo": modelo, "fotos": fotos})


@gestor_required
@require_POST
def gestion_foto_borrar(request, pk):
    foto = get_object_or_404(FotoModelo, pk=pk)
    if foto.modelo.organizacion != _org(request):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    foto.delete()
    return redirect(request.META.get("HTTP_REFERER", "/gestion/"))


@gestor_required
def gestion_marcas(request):
    org = _org(request)
    if request.method == "POST":
        form = MarcaForm(request.POST, request.FILES)
        if form.is_valid():
            m = form.save(commit=False)
            m.organizacion = org
            m.save()
            return redirect("optica:gestion_marcas")
    else:
        form = MarcaForm()
    marcas = Marca.objects.filter(organizacion=org)
    return render(request, "optica/gestion/marcas.html", {"form": form, "marcas": marcas})


@gestor_required
@require_POST
def gestion_marca_borrar(request, pk):
    org = _org(request)
    marca = get_object_or_404(Marca, pk=pk, organizacion=org)
    marca.delete()
    return redirect("optica:gestion_marcas")


@gestor_required
def gestion_categorias(request):
    org = _org(request)
    if request.method == "POST":
        form = CategoriaForm(request.POST)
        if form.is_valid():
            c = form.save(commit=False)
            c.organizacion = org
            c.save()
            return redirect("optica:gestion_categorias")
    else:
        form = CategoriaForm()
    categorias = Categoria.objects.filter(organizacion=org)
    return render(request, "optica/gestion/categorias.html", {"form": form, "categorias": categorias})


@gestor_required
@require_POST
def gestion_categoria_borrar(request, pk):
    org = _org(request)
    cat = get_object_or_404(Categoria, pk=pk, organizacion=org)
    cat.delete()
    return redirect("optica:gestion_categorias")


@gestor_required
def gestion_consultas(request):
    org = _org(request)
    qs = Consulta.objects.filter(organizacion=org)
    if request.GET.get("solo") == "sinleer":
        qs = qs.filter(leida=False)
    return render(request, "optica/gestion/consultas.html", {"consultas": qs})


@gestor_required
def gestion_consulta_detalle(request, pk):
    org = _org(request)
    consulta = get_object_or_404(Consulta, pk=pk, organizacion=org)
    if request.method == "POST":
        consulta.leida = True
        consulta.save(update_fields=["leida"])
        return redirect("optica:gestion_consultas")
    return render(request, "optica/gestion/consulta_detail.html", {"consulta": consulta})


@gestor_required
def gestion_citas(request):
    org = _org(request)
    citas = Cita.objects.filter(organizacion=org)
    return render(request, "optica/gestion/citas.html", {"citas": citas})


@gestor_required
@require_POST
def gestion_cita_estado(request, pk):
    org = _org(request)
    cita = get_object_or_404(Cita, pk=pk, organizacion=org)
    estado = request.POST.get("estado")
    if estado in dict(Cita._meta.get_field("estado").choices):
        cita.estado = estado
        cita.save(update_fields=["estado"])
    return redirect("optica:gestion_citas")


@gestor_required
def gestion_ajustes(request):
    org = _org(request)
    ajustes = Ajustes.for_org(org)
    if request.method == "POST":
        form = AjustesForm(request.POST, request.FILES, instance=ajustes)
        if form.is_valid():
            form.save()
            return redirect("optica:gestion_ajustes")
    else:
        form = AjustesForm(instance=ajustes)
    return render(request, "optica/gestion/ajustes.html", {"form": form})


@gestor_required
def gestion_novedades(request):
    org = _org(request)
    if request.method == "POST":
        form = EntradaForm(request.POST, request.FILES)
        if form.is_valid():
            e = form.save(commit=False)
            e.organizacion = org
            e.save()
            return redirect("optica:gestion_novedades")
    else:
        form = EntradaForm()
    entradas = Entrada.objects.filter(organizacion=org)
    return render(request, "optica/gestion/novedades.html", {"form": form, "entradas": entradas})


@gestor_required
def gestion_historial(request):
    from core.models import Auditoria
    org = _org(request)
    qs = Auditoria.objects.filter(organizacion=org).order_by("-fecha")[:100]
    return render(request, "optica/gestion/historial.html", {"auditorias": qs})


@gestor_required
def gestion_qr(request, pk):
    org = _org(request)
    modelo = get_object_or_404(Modelo, pk=pk, organizacion=org)
    import qrcode
    from io import BytesIO
    from django.http import HttpResponse
    url = request.build_absolute_uri(reverse("optica:modelo_detail", args=[modelo.slug]))
    img = qrcode.make(url)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    resp = HttpResponse(buf.getvalue(), content_type="image/png")
    resp["Content-Disposition"] = f'attachment; filename="qr-{modelo.slug}.png"'
    return resp
