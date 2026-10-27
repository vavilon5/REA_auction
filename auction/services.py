from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError
from .models import Auction, Bid, Event, User


class Conflict(APIException):
    status_code = 409
    default_detail = "Конфликт состояния"


class Locked(APIException):
    status_code = 423
    default_detail = "Аукцион приостановлен"


def eligible(user):
    if not user.is_active or not user.email_verified:
        raise PermissionDenied(
            "Требуется активная учётная запись с подтверждённой почтой"
        )


def event(auction, actor, action, reason=""):
    Event.objects.create(auction=auction, actor=actor, action=action, reason=reason)


@transaction.atomic
def place_bid(auction_id, user, amount, key):
    a = Auction.objects.select_for_update().get(pk=auction_id)
    # Пользователь повторно читается внутри транзакции; блокировка не берётся
    # по пользователю, чтобы избежать взаимной блокировки разных аукционов.
    eligible(User.objects.get(pk=user.pk))
    if a.owner_id == user.pk:
        raise PermissionDenied("Нельзя ставить на свою задачу")
    old = Bid.objects.filter(auction=a, bidder=user, idempotency_key=key).first()
    if old:
        if old.auction_id != a.pk or old.amount_kopecks != amount:
            raise Conflict("Ключ уже использован с другим телом запроса")
        return old, False
    if a.status != Auction.Status.OPEN or timezone.now() >= a.ends_at:
        raise Conflict("Приём ставок закрыт")
    if amount > a.budget_kopecks:
        raise ValidationError({"amount_kopecks": "Ставка превышает бюджет"})
    if Bid.objects.filter(auction=a, bidder=user).exists():
        raise Conflict("Разрешена одна неизменяемая ставка на участника")
    b = Bid.objects.create(
        auction=a, bidder=user, amount_kopecks=amount, idempotency_key=key
    )
    event(a, user, "bid_accepted")
    return b, True


@transaction.atomic
def transition(auction_id, user, action, reason=""):
    a = Auction.objects.select_for_update().get(pk=auction_id)
    eligible(User.objects.get(pk=user.pk))
    if action == "submit":
        if a.owner_id != user.pk:
            raise PermissionDenied()
        if a.status not in ("draft", "rejected"):
            raise Conflict()
        target = "review"
    else:
        if not user.has_perm("auction.moderate_auction") or a.owner_id == user.pk:
            raise PermissionDenied("Нельзя модерировать свою задачу")
        if a.status != "review":
            raise Conflict()
        if not reason.strip():
            raise ValidationError({"reason": "Укажите причину решения"})
        target = "open" if action == "approve" else "rejected"
    if target in ("review", "open") and (
        a.ends_at <= timezone.now() or a.due_at <= a.ends_at
    ):
        raise ValidationError("Проверьте сроки")
    a.status = target
    a.moderation_reason = reason
    a.save(update_fields=["status", "moderation_reason"])
    event(a, user, action, reason)
    return a


@transaction.atomic
def close_auction(auction_id):
    a = Auction.objects.select_for_update().get(pk=auction_id)
    if a.status != "open" or timezone.now() < a.ends_at:
        return a
    # Исключение участника меняет вторую цену. Вместо тихого перерасчёта
    # останавливаем торги и сохраняем историю для решения следующего спринта.
    if (
        not a.owner.is_active
        or not a.owner.email_verified
        or a.bids.filter(models_invalid_bidder()).exists()
    ):
        a.status = "paused"
        a.save(update_fields=["status"])
        event(a, None, "paused", "Участник заблокирован или допуск отозван")
        return a
    best = list(a.bids.order_by("amount_kopecks", "created_at", "id")[:2])
    a.status = "closed"
    a.closed_at = timezone.now()
    if best:
        a.winner_id = best[0].bidder_id
        a.payment_kopecks = (
            best[1].amount_kopecks if len(best) > 1 else a.budget_kopecks
        )
    a.save(update_fields=["status", "closed_at", "winner", "payment_kopecks"])
    event(a, None, "closed")
    return a


def models_invalid_bidder():
    from django.db.models import Q

    return Q(bidder__is_active=False) | Q(bidder__email_verified=False)
