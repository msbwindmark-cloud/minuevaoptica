from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Modelo, Entrada


class ModeloSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Modelo.objects.filter(visible=True)

    def lastmod(self, obj):
        return obj.actualizado

    def location(self, obj):
        return f"/catalogo/{obj.slug}/"


class EntradaSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        return Entrada.objects.filter(publicada=True)

    def lastmod(self, obj):
        return obj.fecha

    def location(self, obj):
        return f"/novedades/{obj.slug}/"


class StaticSitemap(Sitemap):
    priority = 0.5
    changefreq = "monthly"

    def items(self):
        return ["home", "catalogo", "marcas", "encuentra", "favoritos", "comparar", "citas", "novedades", "contacto", "nosotros"]

    def location(self, item):
        return reverse(f"optica:{item}")