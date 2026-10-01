from rest_framework.routers import SimpleRouter

from .views import PagamentoViewSet


router = SimpleRouter()
router.register("pagamentos", PagamentoViewSet, basename="pagamentos")

urlpatterns = router.urls
