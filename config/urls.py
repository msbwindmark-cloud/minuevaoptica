from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

from optica.sitemaps import ModeloSitemap, EntradaSitemap, StaticSitemap

sitemaps = {"modelos": ModeloSitemap, "entradas": EntradaSitemap, "static": StaticSitemap}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("i18n/", include("django.conf.urls.i18n")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("optica.urls")),
]

if settings.DEBUG:
    try:
        urlpatterns += [path("__reload__/", include("django_browser_reload.urls"))]
    except Exception:
        pass

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
