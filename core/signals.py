from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver

from .models import TenantModel, Auditoria, get_audit_context, Perfil


def _is_tenant_model(sender):
    try:
        return issubclass(sender, TenantModel) and not getattr(sender._meta, "abstract", True) and sender is not Auditoria
    except Exception:
        return False


EXCLUDE_FIELDS = {
    "password", "last_login", "token", "access_token", "refresh_token",
    "vapid_private_key", "vapid_public_key", "firma_base64",
}

_old_cache = {}


def _ctx():
    return get_audit_context() or {}


def _user(ctx):
    u = ctx.get("user")
    if u is not None and getattr(u, "is_authenticated", False):
        return u
    return None


def _org(instance, ctx):
    org = getattr(instance, "organizacion", None)
    if org is None:
        org = ctx.get("organizacion")
    return org


def _create_audit(instance_or_none, sender, accion, cambios=None, objeto_repr=None, usuario_nombre_override=None):
    ctx = _ctx()
    user = _user(ctx)
    org = None
    if instance_or_none is not None:
        org = _org(instance_or_none, ctx)
    else:
        org = ctx.get("organizacion")
    ct = None
    oid = ""
    repr_ = objeto_repr or ""
    if instance_or_none is not None:
        ct = ContentType.objects.get_for_model(type(instance_or_none))
        oid = str(getattr(instance_or_none, "pk", "") or "")
        if not repr_:
            repr_ = str(instance_or_none)[:255]
    if usuario_nombre_override is not None:
        nombre = usuario_nombre_override
    else:
        nombre = getattr(user, "username", "") if user else ctx.get("usuario_nombre", "")
    Auditoria.objects.create(
        organizacion=org,
        usuario=user,
        usuario_nombre=nombre,
        accion=accion,
        content_type=ct,
        object_id=oid,
        objeto_repr=repr_[:255],
        cambios=cambios or {},
        ip=ctx.get("ip"),
        user_agent=ctx.get("user_agent", ""),
        ruta=ctx.get("ruta", ""),
        metodo=ctx.get("metodo", ""),
    )


@receiver(pre_save)
def audit_pre_save(sender, instance, **kwargs):
    if not _is_tenant_model(sender):
        return
    if getattr(instance, "pk", None):
        try:
            old = sender.all_objects.get(pk=instance.pk)
            _old_cache[(sender, instance.pk)] = old
        except sender.DoesNotExist:
            pass


@receiver(post_save)
def audit_post_save(sender, instance, created, **kwargs):
    if not _is_tenant_model(sender):
        return
    old = None
    if not created:
        old = _old_cache.pop((sender, instance.pk), None)
    cambios = {}
    if created:
        for field in instance._meta.fields:
            name = field.name
            if name in EXCLUDE_FIELDS or name in ("id", "pk", "creado", "actualizado", "organizacion"):
                continue
            if field.many_to_many:
                continue
            try:
                val = getattr(instance, name)
            except Exception:
                continue
            cambios[name] = [None, str(val) if val is not None else None]
    if not created and old is not None:
        for field in instance._meta.fields:
            name = field.name
            if name in EXCLUDE_FIELDS:
                continue
            if field.many_to_many:
                continue
            try:
                old_val = getattr(old, name)
                new_val = getattr(instance, name)
            except Exception:
                continue
            if old_val != new_val:
                cambios[name] = [str(old_val) if old_val is not None else None,
                                str(new_val) if new_val is not None else None]
                if name in ("password",):
                    cambios[name] = ["***", "***"]
    # nunca guardar contraseñas reales
    if "password" in cambios:
        cambios["password"] = ["***", "***"]
    _create_audit(instance, sender, "crear" if created else "editar", cambios=cambios)


@receiver(post_delete)
def audit_post_delete(sender, instance, **kwargs):
    if not _is_tenant_model(sender):
        return
    _create_audit(instance, sender, "borrar", cambios={"deleted": True})


@receiver(user_logged_in)
def audit_login(sender, request, user, **kwargs):
    ctx = get_audit_context() or {}
    # set user in ctx if missing
    if not ctx.get("user"):
        ctx["user"] = user
    org = None
    try:
        org = user.perfil.organizacion
    except Exception:
        org = None
    # temporarily set org context not needed
    Auditoria.objects.create(
        organizacion=org,
        usuario=user,
        usuario_nombre=user.username,
        accion="login",
        objeto_repr=f"login {user.username}",
        ip=ctx.get("ip"),
        user_agent=ctx.get("user_agent", ""),
        ruta=ctx.get("ruta", ""),
        metodo=ctx.get("metodo", ""),
    )


@receiver(user_logged_out)
def audit_logout(sender, request, user, **kwargs):
    ctx = get_audit_context() or {}
    if user is None:
        return
    org = None
    try:
        org = user.perfil.organizacion
    except Exception:
        org = None
    Auditoria.objects.create(
        organizacion=org,
        usuario=user,
        usuario_nombre=getattr(user, "username", ""),
        accion="logout",
        objeto_repr=f"logout {getattr(user, 'username', '')}",
        ip=ctx.get("ip"),
        user_agent=ctx.get("user_agent", ""),
        ruta=ctx.get("ruta", ""),
        metodo=ctx.get("metodo", ""),
    )


@receiver(user_login_failed)
def audit_login_failed(sender, credentials, request, **kwargs):
    ctx = get_audit_context() or {}
    username = credentials.get("username", "")
    org = None
    try:
        u = Perfil.objects.select_related("organizacion").get(user__username=username)
        org = u.organizacion
    except Exception:
        org = None
    Auditoria.objects.create(
        organizacion=org,
        usuario=None,
        usuario_nombre=username,
        accion="login_fallido",
        objeto_repr=f"login fallido {username}",
        ip=ctx.get("ip"),
        user_agent=ctx.get("user_agent", ""),
        ruta=ctx.get("ruta", ""),
        metodo=ctx.get("metodo", ""),
    )
