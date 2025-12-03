from django.core.management.base import BaseCommand
from projects.models import PublicHoliday
from datetime import date


class Command(BaseCommand):
    help = '2025-ös magyar ünnepnapok betöltése'

    def handle(self, *args, **options):
        holidays = [
            (date(2025, 1, 1), "Újév", False),
            (date(2025, 3, 15), "Nemzeti Ünnep", False),
            (date(2025, 4, 18), "Nagypéntek", False),
            (date(2025, 4, 21), "Húsvét", False),
            (date(2025, 5, 1), "Munka Ünnepe", False),
            (date(2025, 5, 2), "Pihenőnap (Máj. 1 után)", False),
            (date(2025, 5, 17), "Áthelyezett Munkanap (Máj. 2 helyett)", True),  # SZOMBAT, DE MUNKA!
            (date(2025, 6, 9), "Pünkösd", False),
            (date(2025, 8, 20), "Államalapítás", False),
            (date(2025, 10, 23), "56-os Forradalom", False),
            (date(2025, 10, 24), "Pihenőnap (Okt. 23 után)", False),
            (date(2025, 10, 18), "Áthelyezett Munkanap (Okt. 24 helyett)", True),  # SZOMBAT, DE MUNKA!
            (date(2025, 11, 1), "Mindenszentek", False),
            (date(2025, 12, 24), "Szenteste", False),
            (date(2025, 12, 25), "Karácsony", False),
            (date(2025, 12, 26), "Karácsony", False),
        ]

        for d, name, is_work in holidays:
            PublicHoliday.objects.get_or_create(
                date=d,
                defaults={'name': name, 'is_workday': is_work}
            )

        self.stdout.write(self.style.SUCCESS('Ünnepek sikeresen feltöltve!'))