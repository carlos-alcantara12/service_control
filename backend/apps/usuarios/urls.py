from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import LoginView, LogoutView, UsuarioViewSet


router = SimpleRouter()
router.register("usuarios", UsuarioViewSet, basename="usuarios")

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
] + router.urls
