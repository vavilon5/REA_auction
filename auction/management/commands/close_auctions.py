import time
from django.core.management.base import BaseCommand
from django.utils import timezone
from auction.models import Auction
from auction.services import close_auction


class Command(BaseCommand):
    help = "Закрыть просроченные торги; --loop опрашивает каждые 10 секунд"

    def add_arguments(self, parser):
        parser.add_argument("--loop", action="store_true")

    def handle(self, *args, **options):
        while True:
            ids = list(
                Auction.objects.filter(
                    status="open", ends_at__lte=timezone.now()
                ).values_list("id", flat=True)
            )
            for pk in ids:
                close_auction(pk)
                self.stdout.write(f"Обработан аукцион {pk}")
            if not options["loop"]:
                break
            time.sleep(10)
