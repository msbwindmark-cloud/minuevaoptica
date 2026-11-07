from django.contrib import admin
from .models import (
    Ajustes, Marca, Categoria, Modelo, FotoModelo, Consulta, Cita, Entrada, Opinion, EnvioCorreo,
)


@admin.register(Ajustes)
class AjustesAdmin(admin.ModelAdmin):
    list_display = ("organizacion", "nombre_comercial", "telefono", "email")


@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "organizacion", "visible", "orden")
    list_filter = ("visible", "organizacion")
    search_fields = ("nombre",)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "organizacion", "visible", "orden")
    list_filter = ("visible", "organizacion")


@admin.register(Modelo)
class ModeloAdmin(admin.ModelAdmin):
    list_display = ("nombre", "marca", "categoria", "visible", "destacado", "novedad", "precio")
    list_filter = ("visible", "destacado", "novedad", "genero", "forma", "organizacion")
    search_fields = ("nombre", "marca__nombre", "color")
    prepopulated_fields = {}


@admin.register(FotoModelo)
class FotoModeloAdmin(admin.ModelAdmin):
    list_display = ("modelo", "orden")
    list_filter = ("modelo__organizacion",)


@admin.register(Consulta)
class ConsultaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "telefono", "email", "fecha", "leida", "modelo")
    list_filter = ("leida", "organizacion")


@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "telefono", "fecha_hora", "motivo", "estado")
    list_filter = ("estado", "organizacion")


@admin.register(Entrada)
class EntradaAdmin(admin.ModelAdmin):
    list_display = ("titulo", "publicada", "fecha")
    list_filter = ("publicada", "organizacion")


@admin.register(Opinion)
class OpinionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "visible", "fecha")
    list_filter = ("visible", "organizacion")


@admin.register(EnvioCorreo)
class EnvioCorreoAdmin(admin.ModelAdmin):
    list_display = ("destinatario", "tipo", "estado", "fecha")
    list_filter = ("estado", "organizacion")
    readonly_fields = ("destinatario", "asunto", "tipo", "fecha", "estado", "error")
