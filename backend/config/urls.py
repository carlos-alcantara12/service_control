from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from django.views.generic import RedirectView, TemplateView


urlpatterns = [
    path("", RedirectView.as_view(url="/login/", permanent=False), name="app"),
    path("login/", TemplateView.as_view(template_name="screens/login/index.html"), name="login-page"),
    path("dashboard/", TemplateView.as_view(template_name="screens/dashboard/index.html"), name="dashboard-page"),
    path("ordens/", TemplateView.as_view(template_name="screens/ordens/index.html"), name="ordens-page"),
    path("clientes/", TemplateView.as_view(template_name="screens/clientes/index.html"), name="clientes-page"),
    path("equipamentos/", TemplateView.as_view(template_name="screens/equipamentos/index.html"), name="equipamentos-page"),
    path("orcamentos/", TemplateView.as_view(template_name="screens/orcamentos/index.html"), name="orcamentos-page"),
    path("financeiro/", TemplateView.as_view(template_name="screens/financeiro/index.html"), name="financeiro-page"),
    path("relatorios/", TemplateView.as_view(template_name="screens/relatorios/index.html"), name="relatorios-page"),
    path("usuarios/", TemplateView.as_view(template_name="screens/usuarios/index.html"), name="usuarios-page"),
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
