"""Script de datos de prueba para Óptica Espartinas."""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

from django.contrib.auth.models import User
from django.core.files.base import ContentFile

from core.models import Organizacion, Perfil
from optica.models import Ajustes, Marca, Categoria, Modelo, FotoModelo, Consulta, Cita, Entrada, Opinion
from optica.utils import optimize_image


def make_image(text, color=(200, 210, 230), size=(800, 600)):
    img = Image.new("RGB", size, color)
    draw = ImageDraw.Draw(img)
    draw.text((40, size[1] // 2 - 20), text[:40], fill=(30, 30, 30))
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return ContentFile(buf.getvalue(), name=text.replace(" ", "_") + ".png")


def main():
    org, _ = Organizacion.objects.get_or_create(slug="optica-espartinas", defaults={"nombre": "Óptica Espartinas"})
    user, created = User.objects.get_or_create(username="laura", defaults={"email": "laura@opticaespartinas.local"})
    if created:
        user.set_password("Laura12345!")
        user.save()
    perfil, _ = Perfil.objects.get_or_create(user=user, defaults={"organizacion": org, "rol": "gestor"})
    perfil.organizacion = org
    perfil.rol = "gestor"
    perfil.save()

    ajustes = Ajustes.for_org(org)
    ajustes.nombre_comercial = "Óptica Espartinas"
    ajustes.direccion = "C/ Ejemplo 12, Espartinas (Sevilla)"
    ajustes.telefono = "955 00 00 00"
    ajustes.whatsapp = "34600000000"
    ajustes.email = "info@opticaespartinas.local"
    ajustes.horario = "Lunes a Viernes: 10:00-14:00 y 17:00-20:30\nSábados: 10:00-14:00"
    ajustes.texto_portada = "Tu óptica de confianza en Espartinas"
    ajustes.color_primario = "#1e3a5f"
    ajustes.color_secundario = "#c9a227"
    ajustes.save()

    marcas_data = ["Ray-Ban", "Oakley", "Gucci", "Prada", "Tom Ford"]
    marcas = {}
    for i, nombre in enumerate(marcas_data):
        m, _ = Marca.objects.get_or_create(organizacion=org, slug=nombre.lower(), defaults={"nombre": nombre, "orden": i, "visible": True})
        marcas[nombre] = m

    cats_data = ["Gafas de sol", "Monturas graduadas", "Infantil", "Deportivas", "Accesorios"]
    cats = {}
    for i, nombre in enumerate(cats_data):
        c, _ = Categoria.objects.get_or_create(organizacion=org, slug=nombre.lower().replace(" ", "-"), defaults={"nombre": nombre, "orden": i, "visible": True})
        cats[nombre] = c

    formas = ["redonda", "cuadrada", "aviador", "cat-eye", "rectangular", "ovalada"]
    materiales = ["acetato", "metal", "titanio", "tr90", "combinado"]
    generos = ["mujer", "hombre", "unisex", "infantil"]

    modelos_creados = []
    for i in range(18):
        marca = marcas[marcas_data[i % len(marcas_data)]]
        cat = cats[cats_data[i % len(cats_data)]]
        nombre = f"Modelo {i+1:02d}"
        m, created = Modelo.objects.get_or_create(
            organizacion=org, slug=f"{marca.slug}-{nombre.lower().replace(' ', '-')}",
            defaults={
                "marca": marca, "categoria": cat, "nombre": nombre,
                "descripcion_corta": "Montura ligera y cómoda.",
                "descripcion_larga": "Diseño elegante con materiales de calidad. Incluye funda y paño.",
                "precio": 89 + i * 12,
                "material": materiales[i % len(materiales)],
                "forma": formas[i % len(formas)],
                "ancho_lente": str(50 + (i % 5) * 2),
                "puente": "18", "varilla": "140",
                "color": ["negro", "carey", "dorado", "plateado", "azul"][i % 5],
                "genero": generos[i % len(generos)],
                "destacado": i < 4,
                "novedad": i % 3 == 0,
                "visible": True,
            },
        )
        if created:
            img = make_image(f"{marca.nombre} {nombre}", color=(180 + (i*7)%60, 200, 220))
            FotoModelo.objects.create(modelo=m, imagen=img, alt=nombre, organizacion=org)
            if i < 3:
                # imagen transparente para el probador
                timg = Image.new("RGBA", (400, 120), (0, 0, 0, 0))
                td = ImageDraw.Draw(timg)
                td.rectangle((20, 40, 380, 80), fill=(30, 30, 30, 180))
                tbuf = BytesIO()
                timg.save(tbuf, format="PNG")
                tbuf.seek(0)
                m.foto_probador.save(f"probador_{i}.png", ContentFile(tbuf.getvalue()), save=True)
        modelos_creados.append(m)

    # Consultas
    for i in range(6):
        Consulta.objects.get_or_create(
            organizacion=org, nombre=f"Cliente {i+1}", telefono=f"60000000{i}",
            defaults={"email": f"cliente{i+1}@example.com", "mensaje": "Me interesa un modelo de sol.", "leida": i % 2 == 0},
        )

    # Citas
    from django.utils import timezone
    for i in range(4):
        Cita.objects.get_or_create(
            organizacion=org, nombre=f"Paciente {i+1}", telefono=f"61100000{i}",
            defaults={"fecha_hora": timezone.now() + timezone.timedelta(days=i+1, hours=10), "motivo": "revision", "estado": "pendiente"},
        )

    # Novedades
    for i in range(3):
        Entrada.objects.get_or_create(
            organizacion=org, slug=f"novedad-{i+1}",
            defaults={"titulo": f"Novedad {i+1}", "texto": "Texto de ejemplo de la entrada del blog.", "publicada": True},
        )

    # Opiniones
    for i in range(3):
        Opinion.objects.get_or_create(
            organizacion=org, nombre=f"Cliente feliz {i+1}",
            defaults={"texto": "Excelente atención y monturas preciosas.", "visible": True},
        )

    print("Seed completado.")


if __name__ == "__main__":
    main()
