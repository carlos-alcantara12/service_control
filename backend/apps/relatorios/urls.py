from rest_framework.routers import SimpleRouter

from .views import RelatorioViewSet


router = SimpleRouter()
router.register("relatorios", RelatorioViewSet, basename="relatorios")

urlpatterns = router.urls
