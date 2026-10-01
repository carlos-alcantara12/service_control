from rest_framework.routers import SimpleRouter

from .views import ClienteViewSet


router = SimpleRouter()
router.register("clientes", ClienteViewSet, basename="clientes")

urlpatterns = router.urls
