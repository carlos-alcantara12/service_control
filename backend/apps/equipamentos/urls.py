from rest_framework.routers import SimpleRouter

from .views import EquipamentoViewSet


router = SimpleRouter()
router.register("equipamentos", EquipamentoViewSet, basename="equipamentos")

urlpatterns = router.urls
