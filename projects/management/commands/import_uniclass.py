# projects/management/commands/import_uniclass.py

from django.core.management.base import BaseCommand
from django.db import transaction  # <--- EZ AZ ÚJ VARÁZSSZÓ
from projects.models import UniclassNode
import openpyxl
import os


class Command(BaseCommand):
    help = 'Uniclass 2015 Excel táblázatok importálása (Gyorsított)'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Az Excel fájl elérési útja')
        parser.add_argument('table_code', type=str, help='Uniclass tábla kódja (pl. Pr, Ef)')

    def handle(self, *args, **options):
        file_path = options['file_path']
        table_code = options['table_code']

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'HIBA: A fájl nem található: {file_path}'))
            return

        self.stdout.write(f'--- Importálás indítása: {table_code} tábla ---')
        self.stdout.write('Excel betöltése... (ez eltarthat pár másodpercig)')

        try:
            wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)  # read_only gyorsabb
            sheet = wb.active
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Hiba: {e}'))
            return

        rows = list(sheet.iter_rows(min_row=2, values_only=True))
        # Rendezés, hogy a szülők előbb legyenek (kód szerint növekvő)
        rows.sort(key=lambda x: x[0] if x[0] else "")

        total_rows = len(rows)
        self.stdout.write(f'{total_rows} sor feldolgozása egyben...')

        # CACHE: Memóriában tároljuk a már létrehozott szülőket, hogy ne kelljen mindig az DB-hez fordulni
        # Ez hatalmasat gyorsít!
        parent_cache = {}

        # Előtöltjük a cache-t a már létező elemekkel (ha újra importálsz)
        existing_nodes = UniclassNode.objects.filter(table=table_code).values('code', 'id')
        for node in existing_nodes:
            parent_cache[node['code']] = node['id']

        created_count = 0

        # --- TRANZAKCIÓ INDÍTÁSA ---
        # Ez blokkolja az írást a végéig, így villámgyors lesz
        try:
            with transaction.atomic():
                for row in rows:
                    code_raw = row[0]
                    title = row[1]

                    if not code_raw: continue
                    code = code_raw.strip()

                    # Szülő keresése a CACHE-ből (nem DB-ből!)
                    parts = code.split('_')
                    parent_id = None

                    if len(parts) > 1:
                        parent_code = "_".join(parts[:-1])
                        parent_id = parent_cache.get(parent_code)  # O(1) gyorsaságú keresés

                    # Létrehozás
                    # update_or_create helyett create-et használunk vagy get_or_create-et
                    # A gyorsaság miatt most feltételezzük, hogy inkább frissítünk/létrehozunk
                    obj, created = UniclassNode.objects.update_or_create(
                        code=code,
                        defaults={
                            'title_en': title,
                            'table': table_code,
                            'parent_id': parent_id  # Közvetlenül ID-t adunk át
                        }
                    )

                    # Betesszük az új elemet is a cache-be, hogy a gyerekei megtalálják
                    parent_cache[code] = obj.id

                    if created: created_count += 1

                    if created_count % 1000 == 0:
                        self.stdout.write(f'... {created_count} új elem feldolgozva')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Hiba történt mentés közben: {e}'))
            return

        self.stdout.write(self.style.SUCCESS(f'KÉSZ! Feldolgozva. Összes elem az adatbázisban: {len(parent_cache)}'))