"""Маршруты API аукциона и аутентификации."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from auction.views import (
    AuctionViewSet,
    CategoryViewSet,
    csrf,
    me,
    signin,
    signout,
)

router = DefaultRouter()
router.register("auctions", AuctionViewSet, basename="auctions")
router.register("categories", CategoryViewSet)

urlpatterns = [
    path("api/", include(router.urls)),
    path("api/auth/csrf/", csrf),
    path("api/auth/login/", signin),
    path("api/auth/logout/", signout),
    path("api/auth/me/", me),
]

urlpatterns += [
    path(
        "api-auth/",
        include("rest_framework.urls", namespace="rest_framework"),
    ),
]
