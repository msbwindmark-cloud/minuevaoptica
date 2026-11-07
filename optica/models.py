import os
from decimal import Decimal

from django.db import models
from django.utils.text import slugify
from django.utils import timezone

from core.models import TenantModel
from .utils import optimize_image


GENERO_CHOICES = [
    ("mujer", "Mujer"),
    ("hombre", "Hombre"),
    ("unisex", "Unisex"),
    ("infantil", "Infantil"),
]

FORMA_CHOICES = [
    ("redonda", "Redonda"),
    ("cuadrada", "Cuadrada"),
    ("aviador", "Aviador"),
    ("cat-eye", "Cat-eye"),
    ("rectangular", "Rectangular"),
    ("ovalada", "Ovalada"),
    ("otra", "Otra"),
]

MATERIAL_CHOICES = [
    ("acetato", "Acetato"),
    ("metal", "Metal"),
    ("titanio", "Titanio"),
    ("tr90", "TR90"),
    ("combinado", "Combinado"),
    ("otro", "Otro"),
]

MOTIVO_CITA = [
    ("revision", "Revisión de vista"),
    ("adaptacion", "Adaptación de lentillas"),
    ("reparacion", "Reparación/ajuste"),
    ("compra", "Elegir montura"),
    ("otro", "Otro"),
]

ESTADO_CITA = [
    ("pendiente", "Pendiente"),
    ("confirmada", "Confirmada"),
    ("cancelada", "Cancelada"),
    ("realizada", "Realizada"),
]


class Ajustes(TenantModel):
    nombre_comercial = models.CharField(max_length=120, default="Óptica")
    direccion = models.CharField(max_length=255, blank=True)
    telefono = models.CharField(max_length=30, blank=True)
    whatsapp = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    horario = models.TextField(blank=True, help_text="Texto libre con horario")
    vacaciones = models.TextField(blank=True, help_text="Aviso de vacaciones/festivos")
    google_maps_url = models.URLField(blank=True)
    google_reviews_url = models.URLField(blank=True, help_text="Enlace para dejar reseña en Google")
    instagram = models.URLField(blank=True)
    facebook = models.URLField(blank=True)
    tiktok = models.URLField(blank=True)
    texto_portada = models.TextField(blank=True)
    logo = models.ImageField(upload_to="optica/logos/", blank=True, null=True)
    color_primario = models.CharField(max_length=20, default="#1e3a5f")
    color_secundario = models.CharField(max_length=20, default="#c9a227")
    hora_apertura = models.TimeField(default="10:00")
    hora_cierre = models.TimeField(default="20:30")
    cerrado = models.BooleanField(default=False, help_text="Marcar si la tienda está cerrada temporalmente")

    class Meta:
        verbose_name = "Ajustes"
        verbose_name_plural = "Ajustes"

    def save(self, *args, **kwargs):
        if self.logo:
            optimize_image(self.logo)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Ajustes {self.organizacion}"

    @classmethod
    def for_org(cls, org):
        obj, _ = cls.objects.get_or_create(organizacion=org, defaults={"nombre_comercial": org.nombre})
        return obj


class Marca(TenantModel):
    nombre = models.CharField(max_length=80)
    slug = models.SlugField(max_length=90, blank=True)
    logo = models.ImageField(upload_to="optica/marcas/", blank=True, null=True)
    orden = models.PositiveIntegerField(default=0)
    visible = models.BooleanField(default=True)

    class Meta:
        ordering = ["orden", "nombre"]
        verbose_name = "Marca"
        verbose_name_plural = "Marcas"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        if self.logo:
            optimize_image(self.logo)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


class Categoria(TenantModel):
    nombre = models.CharField(max_length=80)
    slug = models.SlugField(max_length=90, blank=True)
    orden = models.PositiveIntegerField(default=0)
    visible = models.BooleanField(default=True)

    class Meta:
        ordering = ["orden", "nombre"]
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


class Modelo(TenantModel):
    marca = models.ForeignKey(Marca, on_delete=models.PROTECT, related_name="modelos")
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name="modelos")
    nombre = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, blank=True)
    descripcion_corta = models.CharField(max_length=255, blank=True)
    descripcion_larga = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    precio_texto = models.CharField(max_length=60, blank=True, help_text="Ej. 'Consultar en tienda'")
    material = models.CharField(max_length=20, choices=MATERIAL_CHOICES, default="acetato")
    forma = models.CharField(max_length=20, choices=FORMA_CHOICES, default="redonda")
    ancho_lente = models.CharField(max_length=20, blank=True)
    puente = models.CharField(max_length=20, blank=True)
    varilla = models.CharField(max_length=20, blank=True)
    color = models.CharField(max_length=60, blank=True)
    genero = models.CharField(max_length=20, choices=GENERO_CHOICES, default="unisex")
    destacado = models.BooleanField(default=False)
    novedad = models.BooleanField(default=False)
    agotado = models.BooleanField(default=False)
    visible = models.BooleanField(default=True)
    foto_probador = models.ImageField(upload_to="optica/probador/", blank=True, null=True, help_text="PNG con fondo transparente")
    fecha_alta = models.DateField(default=timezone.now)
    orden = models.PositiveIntegerField(default=0)
    vistas = models.PositiveIntegerField(default=0)
    guardados = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-fecha_alta", "-id"]
        verbose_name = "Modelo"
        verbose_name_plural = "Modelos"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(f"{self.marca.nombre}-{self.nombre}")
            self.slug = base
        if self.foto_probador:
            optimize_image(self.foto_probador, max_size=800)
        # ensure unique slug per org
        if self.slug:
            qs = Modelo.all_objects.filter(organizacion=self.organizacion, slug=self.slug)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            n = 1
            original = self.slug
            while qs.exists():
                self.slug = f"{original}-{n}"
                n += 1
                qs = Modelo.all_objects.filter(organizacion=self.organizacion, slug=self.slug)
                if self.pk:
                    qs = qs.exclude(pk=self.pk)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.marca} {self.nombre}"

    @property
    def foto_portada(self):
        return self.fotos.order_by("orden", "id").first()

    @property
    def precio_display(self):
        if self.precio is not None:
            return f"Desde {self.precio} €"
        if self.precio_texto:
            return self.precio_texto
        return "Consultar en tienda"


class FotoModelo(TenantModel):
    modelo = models.ForeignKey(Modelo, on_delete=models.CASCADE, related_name="fotos")
    imagen = models.ImageField(upload_to="optica/modelos/")
    alt = models.CharField(max_length=120, blank=True)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["orden", "id"]
        verbose_name = "Foto de modelo"
        verbose_name_plural = "Fotos de modelo"

    def save(self, *args, **kwargs):
        # heredar organizacion del modelo si falta
        if not self.organizacion_id and self.modelo_id:
            self.organizacion = self.modelo.organizacion
        if self.imagen:
            optimize_image(self.imagen)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Foto {self.modelo}"


class Consulta(TenantModel):
    nombre = models.CharField(max_length=120)
    telefono = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    mensaje = models.TextField()
    modelo = models.ForeignKey(Modelo, on_delete=models.SET_NULL, null=True, blank=True, related_name="consultas")
    fecha = models.DateTimeField(auto_now_add=True)
    leida = models.BooleanField(default=False)
    consentimiento = models.BooleanField(default=False)
    consentimiento_fecha = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "Consulta"
        verbose_name_plural = "Consultas"

    def __str__(self):
        return f"{self.nombre} ({self.fecha:%d/%m/%Y})"


class Cita(TenantModel):
    nombre = models.CharField(max_length=120)
    telefono = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    fecha_hora = models.DateTimeField()
    motivo = models.CharField(max_length=20, choices=MOTIVO_CITA, default="revision")
    estado = models.CharField(max_length=20, choices=ESTADO_CITA, default="pendiente")
    notas = models.TextField(blank=True)
    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["fecha_hora"]
        verbose_name = "Cita"
        verbose_name_plural = "Citas"

    def __str__(self):
        return f"{self.nombre} - {self.fecha_hora:%d/%m %H:%M}"


class Entrada(TenantModel):
    titulo = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, blank=True)
    texto = models.TextField()
    imagen = models.ImageField(upload_to="optica/blog/", blank=True, null=True)
    publicada = models.BooleanField(default=False)
    fecha = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "Entrada"
        verbose_name_plural = "Entradas"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)
        if self.imagen:
            optimize_image(self.imagen)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.titulo


class Opinion(TenantModel):
    nombre = models.CharField(max_length=80)
    texto = models.TextField()
    visible = models.BooleanField(default=True)
    fecha = models.DateField(default=timezone.now)

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "Opinión"
        verbose_name_plural = "Opiniones"

    def __str__(self):
        return self.nombre


class Pagina(TenantModel):
    slug = models.SlugField(max_length=60)
    titulo = models.CharField(max_length=150)
    contenido = models.TextField()
    publicada = models.BooleanField(default=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("organizacion", "slug")
        verbose_name = "Página"
        verbose_name_plural = "Páginas"

    def __str__(self):
        return self.titulo


class PushSubscription(TenantModel):
    user = models.ForeignKey("auth.User", on_delete=models.CASCADE, related_name="push_subscriptions")
    endpoint = models.URLField(max_length=500, unique=True)
    p256dh = models.CharField(max_length=255)
    auth = models.CharField(max_length=255)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Suscripción push"
        verbose_name_plural = "Suscripciones push"

    def __str__(self):
        return f"{self.user} - {self.endpoint[:40]}"


class RecordatorioRevision(TenantModel):
    nombre = models.CharField(max_length=120)
    email = models.EmailField()
    telefono = models.CharField(max_length=30, blank=True)
    fecha_ultima_revision = models.DateField()
    consentimiento = models.BooleanField(default=True)
    consentimiento_fecha = models.DateTimeField(auto_now_add=True)
    enviado = models.BooleanField(default=False)
    fecha_envio = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-fecha_ultima_revision"]
        verbose_name = "Recordatorio de revisión"
        verbose_name_plural = "Recordatorios de revisión"

    def __str__(self):
        return f"{self.nombre} - {self.fecha_ultima_revision}"


class EnvioCorreo(TenantModel):
    destinatario = models.EmailField()
    asunto = models.CharField(max_length=200)
    tipo = models.CharField(max_length=60)
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, default="enviado")
    error = models.TextField(blank=True)

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "Envío de correo"
        verbose_name_plural = "Envíos de correo"

    def __str__(self):
        return f"{self.destinatario} - {self.asunto}"
