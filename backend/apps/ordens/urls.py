from rest_framework.routers import SimpleRouter

from .views import OrdemServicoViewSet


router = SimpleRouter()
router.register("ordens", OrdemServicoViewSet, basename="ordens")

urlpatterns = router.urls
