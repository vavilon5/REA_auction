from datetime import timedelta
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group, Permission
from django.conf import settings
from django.utils import timezone
from auction.models import User, Category, Auction


class Command(BaseCommand):
    help = "Только локально: создать подтверждённые демонстрационные аккаунты"

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Демонстрационные аккаунты запрещены при DEBUG=0")
        group, _ = Group.objects.get_or_create(name="Модераторы")
        group.permissions.add(Permission.objects.get(codename="moderate_auction"))
        for name in ["owner", "bidder1", "bidder2", "bidder3", "moderator"]:
            u, created = User.objects.get_or_create(
                username=name,
                defaults={"email": name + "@example.edu", "email_verified": True},
            )
            if created:
                u.set_password("Demo-only-2026!")
                u.save()
            if name == "moderator":
                u.groups.add(group)
        cat, _ = Category.objects.get_or_create(name="Помощь с программированием")
        if not Auction.objects.exists():
            Auction.objects.create(
                owner=User.objects.get(username="owner"),
                category=cat,
                title="Разбор алгоритмов поиска",
                description="Провести консультацию по алгоритмам и объяснить сложность поиска.",
                budget_kopecks=150000,
                ends_at=timezone.now() + timedelta(minutes=15),
                due_at=timezone.now() + timedelta(days=2),
                status="draft",
            )
        self.stdout.write(
            "owner, bidder1, bidder2, bidder3, moderator; пароль новых аккаунтов: Demo-only-2026!"
        )
