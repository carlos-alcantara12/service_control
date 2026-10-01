from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.usuarios.urls")),
    path("api/", include("apps.clientes.urls")),
    path("api/", include("apps.equipamentos.urls")),
    path("api/", include("apps.ordens.urls")),
    path("api/", include("apps.orcamentos.urls")),
    path("api/", include("apps.financeiro.urls")),
    path("api/", include("apps.relatorios.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
