from rest_framework.routers import DefaultRouter

from .views import BidViewSet

app_name = "bids"

router = DefaultRouter()
router.register("", BidViewSet, basename="bid")

urlpatterns = router.urls
