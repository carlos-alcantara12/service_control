from rest_framework.routers import SimpleRouter

from .views import OrcamentoViewSet


router = SimpleRouter()
router.register("orcamentos", OrcamentoViewSet, basename="orcamentos")

urlpatterns = router.urls
