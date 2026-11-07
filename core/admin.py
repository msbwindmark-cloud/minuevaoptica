from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Organizacion, Perfil, Auditoria


@admin.register(Organizacion)
class OrganizacionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "slug", "activa", "creada")
    search_fields = ("nombre", "slug")
    prepopulated_fields = {"slug": ("nombre",)}


class PerfilInline(admin.StackedInline):
    model = Perfil
    can_delete = False
    extra = 0


class UserAdmin(BaseUserAdmin):
    inlines = (PerfilInline,)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ("user", "organizacion", "rol", "telefono")
    list_filter = ("rol", "organizacion")
    search_fields = ("user__username", "user__email")


@admin.register(Auditoria)
class AuditoriaAdmin(admin.ModelAdmin):
    list_display = ("fecha", "organizacion", "usuario_nombre", "accion", "objeto_repr", "ip")
    list_filter = ("accion", "organizacion", "content_type")
    search_fields = ("objeto_repr", "usuario_nombre", "ruta")
    readonly_fields = (
        "organizacion", "usuario", "usuario_nombre", "fecha", "accion",
        "content_type", "object_id", "objeto_repr", "cambios", "ip",
        "user_agent", "ruta", "metodo",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
