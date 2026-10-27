from datetime import timedelta
from unittest import skipUnless
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from django.db import connection, close_old_connections
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from django.contrib.auth.models import Permission
from rest_framework.test import APIClient
from rest_framework.exceptions import APIException
from .models import User, Category, Auction, Bid, Event
from .services import place_bid, close_auction, transition


class Fixtures:
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner",
            email="owner@example.edu",
            password="secret",
            email_verified=True,
        )
        self.u = User.objects.create_user(
            username="one",
            email="one@example.edu",
            password="secret",
            email_verified=True,
        )
        self.v = User.objects.create_user(
            username="two",
            email="two@example.edu",
            password="secret",
            email_verified=True,
        )
        self.cat = Category.objects.create(name="Код")
        self.a = Auction.objects.create(
            owner=self.owner,
            category=self.cat,
            title="Учебная задача",
            description="Достаточно длинное описание учебной задачи.",
            budget_kopecks=150000,
            ends_at=timezone.now() + timedelta(hours=1),
            due_at=timezone.now() + timedelta(days=1),
            status="open",
        )
        self.client = APIClient()

    def expire(self):
        Auction.objects.filter(pk=self.a.pk).update(
            ends_at=timezone.now() - timedelta(seconds=1)
        )

    def bid(self, u=None, amount=70000, key="k"):
        return place_bid(self.a.pk, u or self.u, amount, key)


class AuctionTests(Fixtures, TestCase):
    def test_second_price(self):
        self.bid()
        self.bid(self.v, 90000)
        self.expire()
        a = close_auction(self.a.pk)
        self.assertEqual((a.winner_id, a.payment_kopecks), (self.u.pk, 90000))

    def test_three_bids(self):
        third = User.objects.create_user(
            username="three", email="three@example.edu", email_verified=True
        )
        self.bid(third, 110000)
        self.bid(self.v, 90000)
        self.bid()
        self.expire()
        a = close_auction(self.a.pk)
        self.assertEqual((a.winner_id, a.payment_kopecks), (self.u.pk, 90000))

    def test_budget_boundary(self):
        self.bid(amount=150000)
        self.assertEqual(Bid.objects.get().amount_kopecks, 150000)

    def test_edit_private_or_missing_returns_404(self):
        self.a.status = "draft"
        self.a.save()
        self.client.force_authenticate(self.u)
        self.assertEqual(
            self.client.patch(
                f"/api/auctions/{self.a.pk}/", {"title": "Чужая правка"}
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.patch(
                "/api/auctions/999999/", {"title": "Нет объекта"}
            ).status_code,
            404,
        )

    def test_rejected_can_be_edited_and_resubmitted(self):
        self.a.status = "review"
        self.a.save()
        self.v.user_permissions.add(Permission.objects.get(codename="moderate_auction"))
        transition(self.a.pk, self.v, "reject", "Уточнить описание")
        self.client.force_authenticate(self.owner)
        response = self.client.patch(
            f"/api/auctions/{self.a.pk}/",
            {"description": "Исправленное подробное описание консультации."},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(transition(self.a.pk, self.owner, "submit").status, "review")

    def test_single_bid_pays_budget(self):
        self.bid()
        self.expire()
        self.assertEqual(close_auction(self.a.pk).payment_kopecks, 150000)

    def test_no_bids(self):
        self.expire()
        a = close_auction(self.a.pk)
        self.assertEqual(a.status, "closed")
        self.assertIsNone(a.winner_id)
        self.assertIsNone(a.payment_kopecks)

    def test_tie_earliest_wins(self):
        self.bid(self.v)
        self.bid()
        self.expire()
        a = close_auction(self.a.pk)
        self.assertEqual((a.winner_id, a.payment_kopecks), (self.v.pk, 70000))

    def test_repeat_close(self):
        self.bid()
        self.expire()
        first = close_auction(self.a.pk)
        second = close_auction(self.a.pk)
        self.assertEqual(first.closed_at, second.closed_at)
        self.assertEqual(Event.objects.filter(action="closed").count(), 1)

    def test_early_close_no_effect(self):
        self.assertEqual(close_auction(self.a.pk).status, "open")

    def test_repeat_bid_returns_original_even_after_close(self):
        b, created = self.bid()
        self.assertTrue(created)
        self.expire()
        close_auction(self.a.pk)
        repeat, created = self.bid()
        self.assertFalse(created)
        self.assertEqual(b.pk, repeat.pk)
        self.assertEqual(Bid.objects.count(), 1)

    def test_key_body_conflict(self):
        self.bid()
        with self.assertRaises(APIException):
            self.bid(amount=80000)

    def test_second_bid_not_allowed(self):
        self.bid()
        with self.assertRaises(APIException):
            self.bid(key="other")

    def test_owner_cannot_bid(self):
        with self.assertRaises(APIException):
            self.bid(self.owner)

    def test_late_bid(self):
        self.expire()
        with self.assertRaises(APIException):
            self.bid()

    def test_above_budget(self):
        with self.assertRaises(APIException):
            self.bid(amount=150001)

    def test_blocked_user(self):
        self.u.is_active = False
        self.u.save()
        with self.assertRaises(APIException):
            self.bid()

    def test_block_after_bid_pauses(self):
        self.bid()
        self.u.is_active = False
        self.u.save()
        self.expire()
        self.assertEqual(close_auction(self.a.pk).status, "paused")
        self.assertEqual(Bid.objects.count(), 1)

    def test_unverified_denied(self):
        self.u.email_verified = False
        self.u.save()
        self.client.force_authenticate(self.u)
        self.assertEqual(self.client.get("/api/auctions/").status_code, 403)

    def test_anonymous_denied(self):
        self.assertEqual(self.client.get("/api/auctions/").status_code, 403)

    def test_bid_privacy_including_owner(self):
        self.bid()
        for user in [self.v, self.owner]:
            self.client.force_authenticate(user)
            response = self.client.get(f"/api/auctions/{self.a.pk}/bids/")
            self.assertEqual(response.data, [])
            detail = self.client.get(f"/api/auctions/{self.a.pk}/").data
            self.assertNotIn("bids", detail)
            self.assertIsNone(detail["payment_kopecks"])

    def test_bid_api_validation(self):
        self.client.force_authenticate(self.u)
        url = f"/api/auctions/{self.a.pk}/bids/"
        for amount in [0, -1, "no", 1.5]:
            self.assertEqual(
                self.client.post(
                    url,
                    {"amount_kopecks": amount},
                    format="json",
                    HTTP_IDEMPOTENCY_KEY="x",
                ).status_code,
                400,
            )
        self.assertEqual(
            self.client.post(url, {"amount_kopecks": 100}, format="json").status_code,
            400,
        )

    def test_bid_api_replay(self):
        self.client.force_authenticate(self.u)
        url = f"/api/auctions/{self.a.pk}/bids/"
        codes = [
            self.client.post(
                url, {"amount_kopecks": 70000}, format="json", HTTP_IDEMPOTENCY_KEY="x"
            ).status_code
            for _ in range(2)
        ]
        self.assertEqual(codes, [201, 200])

    def test_frozen_and_foreign_edit(self):
        self.client.force_authenticate(self.owner)
        self.assertEqual(
            self.client.patch(
                f"/api/auctions/{self.a.pk}/", {"title": "Другой заголовок"}
            ).status_code,
            409,
        )
        self.client.force_authenticate(self.u)
        self.assertEqual(
            self.client.patch(
                f"/api/auctions/{self.a.pk}/", {"title": "Другой заголовок"}
            ).status_code,
            403,
        )

    def test_moderation(self):
        self.a.status = "draft"
        self.a.save()
        transition(self.a.pk, self.owner, "submit")
        with self.assertRaises(APIException):
            transition(self.a.pk, self.u, "approve", "Проверено")
        self.v.user_permissions.add(Permission.objects.get(codename="moderate_auction"))
        a = transition(self.a.pk, self.v, "approve", "Проверено")
        self.assertEqual(a.status, "open")

    def test_private_draft_hidden(self):
        self.a.status = "draft"
        self.a.save()
        self.client.force_authenticate(self.u)
        self.assertEqual(
            self.client.get(f"/api/auctions/{self.a.pk}/").status_code, 404
        )

    def test_invalid_dates(self):
        self.client.force_authenticate(self.owner)
        body = {
            "category": self.cat.pk,
            "title": "Учебная задача",
            "description": "Достаточно длинное описание задачи.",
            "budget_kopecks": 100,
            "ends_at": timezone.now().isoformat(),
            "due_at": timezone.now().isoformat(),
        }
        self.assertEqual(
            self.client.post("/api/auctions/", body, format="json").status_code, 400
        )

    def test_csrf_login_required(self):
        client = APIClient(enforce_csrf_checks=True)
        self.assertEqual(
            client.post(
                "/api/auth/login/", {"username": "one", "password": "secret"}
            ).status_code,
            403,
        )
        token = client.get("/api/auth/csrf/").data["csrfToken"]
        self.assertEqual(
            client.post(
                "/api/auth/login/",
                {"username": "one", "password": "secret"},
                HTTP_X_CSRFTOKEN=token,
            ).status_code,
            200,
        )

    def test_logout_revokes_session(self):
        self.client.login(username="one", password="secret")
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 200)
        self.assertEqual(self.client.post("/api/auth/logout/").status_code, 204)
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 403)


@skipUnless(
    connection.vendor == "postgresql",
    "Конкурентные блокировки проверяются только на PostgreSQL",
)
class ConcurrentTests(Fixtures, TransactionTestCase):
    def parallel(self, funcs):
        gate = Barrier(len(funcs))

        def run(fn):
            close_old_connections()
            try:
                gate.wait(timeout=10)
                return fn()
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=len(funcs)) as pool:
            return list(pool.map(run, funcs))

    def test_concurrent_repeat(self):
        ids = self.parallel([lambda: self.bid()[0].pk, lambda: self.bid()[0].pk])
        self.assertEqual(ids[0], ids[1])
        self.assertEqual(Bid.objects.count(), 1)

    def test_concurrent_equal_bids(self):
        self.parallel([lambda: self.bid(), lambda: self.bid(self.v)])
        self.assertEqual(Bid.objects.count(), 2)
        self.expire()
        self.parallel(
            [lambda: close_auction(self.a.pk), lambda: close_auction(self.a.pk)]
        )
        self.assertEqual(Event.objects.filter(action="closed").count(), 1)
