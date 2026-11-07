import os
import json
from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image


def optimize_image(image_field, max_size=1600, quality=85):
    """Redimensiona y convierte a WebP una imagen subida."""
    if not image_field:
        return
    try:
        image_field.open()
        img = Image.open(image_field)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        elif img.mode != "RGB":
            img = img.convert("RGB")
        img.thumbnail((max_size, max_size), Image.LANCZOS)
        buf = BytesIO()
        img.save(buf, format="WEBP", quality=quality, method=6)
        buf.seek(0)
        base = os.path.splitext(os.path.basename(image_field.name))[0]
        image_field.save(f"{base}.webp", ContentFile(buf.getvalue()), save=False)
    except Exception:
        # si falla, dejamos la imagen original
        pass


def enviar_push(subs, titulo, cuerpo):
    from django.conf import settings
    try:
        from pywebpush import webpush
    except Exception:
        return 0
    public = getattr(settings, "VAPID_PUBLIC_KEY", "")
    private = getattr(settings, "VAPID_PRIVATE_KEY", "")
    email = getattr(settings, "VAPID_ADMIN_EMAIL", "")
    if not private or not public:
        return 0
    enviados = 0
    for s in subs:
        try:
            webpush(
                subscription_info={"endpoint": s.endpoint, "keys": {"p256dh": s.p256dh, "auth": s.auth}},
                data=json.dumps({"title": titulo, "body": cuerpo}),
                vapid_private_key=private,
                vapid_claims={"sub": f"mailto:{email or 'admin@example.com'}"},
            )
            enviados += 1
        except Exception:
            continue
    return enviados
