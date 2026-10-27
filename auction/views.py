from django.contrib.auth import authenticate, login, logout
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from .models import Auction, Category
from .serializers import (
    AuctionSerializer,
    BidInput,
    BidSerializer,
    CategorySerializer,
    DecisionInput,
)
from .services import eligible, transition, place_bid, Conflict, event


class Admitted(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user.is_authenticated
            and request.user.is_active
            and request.user.email_verified
        )


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def csrf(request):
    return Response({"csrfToken": get_token(request)})


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
@csrf_protect
def signin(request):
    username, password = request.data.get("username"), request.data.get("password")
    if not isinstance(username, str) or not isinstance(password, str):
        raise ValidationError("Передайте username и password")
    user = authenticate(request, username=username, password=password)
    if not user:
        raise PermissionDenied("Неверные данные или нет доступа")
    eligible(user)
    login(request, user)
    return Response(
        {"id": user.pk, "username": user.username, "csrfToken": get_token(request)}
    )


@api_view(["POST"])
def signout(request):
    logout(request)
    return Response(status=204)


@api_view(["GET"])
def me(request):
    eligible(request.user)
    return Response(
        {
            "id": request.user.pk,
            "username": request.user.username,
            "can_moderate": request.user.has_perm("auction.moderate_auction"),
        }
    )


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [Admitted]
    queryset = Category.objects.order_by("id")
    serializer_class = CategorySerializer


class AuctionViewSet(viewsets.ModelViewSet):
    permission_classes = [Admitted]
    serializer_class = AuctionSerializer
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        u = self.request.user
        visible = Q(owner=u) | Q(status__in=["open", "closed"])
        if u.has_perm("auction.moderate_auction"):
            visible |= Q(status="review")
        qs = Auction.objects.filter(visible).order_by("-id")
        if self.action == "list":
            for param in ["status", "category"]:
                value = self.request.query_params.get(param)
                if value:
                    if param == "category" and not value.isdecimal():
                        raise ValidationError(
                            {"category": "Требуется числовой идентификатор"}
                        )
                    qs = qs.filter(**{param: value})
            if self.request.query_params.get("mine") == "1":
                qs = qs.filter(owner=u)
            if self.request.query_params.get("search"):
                qs = qs.filter(
                    Q(title__icontains=self.request.query_params["search"])
                    | Q(description__icontains=self.request.query_params["search"])
                )
        return qs

    def perform_create(self, serializer):
        with transaction.atomic():
            a = serializer.save(owner=self.request.user)
            event(a, self.request.user, "created")

    def partial_update(self, request, *args, **kwargs):
        # Блокировка та же, что при публикации: нельзя изменить условия
        # между проверкой черновика и записью опубликованного аукциона.
        with transaction.atomic():
            a = get_object_or_404(
                self.get_queryset().select_for_update(), pk=kwargs["pk"]
            )
            if a.owner_id != request.user.pk:
                raise PermissionDenied()
            if a.status not in ("draft", "rejected"):
                raise Conflict("Условия заморожены после отправки на модерацию")
            s = self.get_serializer(a, data=request.data, partial=True)
            s.is_valid(raise_exception=True)
            s.save()
            event(a, request.user, "edited")
            return Response(s.data)

    def do_transition(self, request, action):
        a = self.get_object()
        reason = ""
        if action != "submit":
            s = DecisionInput(data=request.data)
            s.is_valid(raise_exception=True)
            reason = s.validated_data["reason"]
        result = transition(a.pk, request.user, action, reason)
        return Response(self.get_serializer(result).data)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        return self.do_transition(request, "submit")

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        return self.do_transition(request, "approve")

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        return self.do_transition(request, "reject")

    @action(detail=True, methods=["get", "post"])
    def bids(self, request, pk=None):
        a = self.get_object()
        if request.method == "GET":
            # Даже заказчик и модератор получают исключительно свои ставки.
            return Response(
                BidSerializer(a.bids.filter(bidder=request.user), many=True).data
            )
        s = BidInput(data=request.data)
        s.is_valid(raise_exception=True)
        key = request.headers.get("Idempotency-Key", "")
        if not key.strip() or len(key) > 80:
            raise ValidationError(
                {"Idempotency-Key": "Укажите непустой ключ длиной до 80 символов"}
            )
        bid, created = place_bid(
            a.pk, request.user, s.validated_data["amount_kopecks"], key
        )
        return Response(BidSerializer(bid).data, status=201 if created else 200)
