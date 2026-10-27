"""Локальная демонстрация по HTTP. Только стандартная библиотека Python."""

import json
import time
from datetime import datetime, timedelta, timezone
from http.cookiejar import CookieJar
from urllib.request import build_opener, HTTPCookieProcessor, Request

BASE = "http://127.0.0.1:8000"


class Client:
    def __init__(self, name):
        self.opener = build_opener(HTTPCookieProcessor(CookieJar()))
        self.token = self.call("GET", "/api/auth/csrf/")["csrfToken"]
        self.token = self.call(
            "POST",
            "/api/auth/login/",
            {"username": name, "password": "Demo-only-2026!"},
        )["csrfToken"]

    def call(self, method, path, data=None, key=None):
        headers = {
            "Content-Type": "application/json",
            "X-CSRFToken": getattr(self, "token", ""),
        }
        if key:
            headers["Idempotency-Key"] = key
        req = Request(
            BASE + path,
            data=json.dumps(data).encode() if data is not None else None,
            headers=headers,
            method=method,
        )
        with self.opener.open(req) as response:
            raw = response.read()
            return json.loads(raw) if raw else None


owner = Client("owner")
mod = Client("moderator")
bidders = [Client("bidder" + str(i)) for i in range(1, 4)]
cat = owner.call("GET", "/api/categories/")["results"][0]["id"]
end = datetime.now(timezone.utc) + timedelta(seconds=12)
a = owner.call(
    "POST",
    "/api/auctions/",
    {
        "title": "Консультация по алгоритмам",
        "description": "Объяснить бинарный поиск и разобрать учебные примеры.",
        "category": cat,
        "budget_kopecks": 150000,
        "ends_at": end.isoformat(),
        "due_at": (end + timedelta(days=1)).isoformat(),
    },
)
path = "/api/auctions/" + str(a["id"]) + "/"
owner.call("POST", path + "submit/", {})
mod.call("POST", path + "approve/", {"reason": "Учебная консультация разрешена"})
for i, (c, amount) in enumerate(zip(bidders, [70000, 90000, 110000])):
    c.call("POST", path + "bids/", {"amount_kopecks": amount}, key="demo-" + str(i))
assert owner.call("GET", path + "bids/") == []
assert len(bidders[0].call("GET", path + "bids/")) == 1
print(
    "Ставки приняты, приватность проверена. Ожидание серверного закрытия до 40 секунд."
)
for _ in range(20):
    a = owner.call("GET", path)
    if a["status"] == "closed":
        assert a["payment_kopecks"] == 90000, a
        assert a["winner_id"] == bidders[0].call("GET", "/api/auth/me/")["id"], a
        print("Успех: bidder1 победил, цена 900 рублей.", BASE + path)
        break
    time.sleep(2)
else:
    print(
        "Торги истекли. Запустите python manage.py close_auctions. Результат:",
        BASE + path,
    )
