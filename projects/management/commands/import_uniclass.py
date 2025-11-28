# projects/management/commands/import_uniclass.py

from django.core.management.base import BaseCommand
from projects.models import UniclassNode
import openpyxl
import os


class Command(BaseCommand):
    help = 'Uniclass 2015 Excel táblázatok importálása (A-N oszlopok, Biztonságos Bulk mód)'

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
        self.stdout.write('Excel beolvasása (A-N oszlopok)...')

        try:
            wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
            sheet = wb.active
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Hiba az Excel megnyitásakor: {e}'))
            return

        excel_rows = []
        for row in sheet.iter_rows(min_row=2, max_col=14, values_only=True):
            if row[0]:
                cleaned_row = [str(cell).strip() if cell is not None else "" for cell in row]
                excel_rows.append(cleaned_row)

        self.stdout.write(f'{len(excel_rows)} sor beolvasva. Adatbázis ellenőrzése...')

        # 1. LÉPÉS: MINDEN LÉTEZŐ ELEM LEKÉRÉSE (JAVÍTÁS: Nincs szűrés táblára!)
        # Így elkerüljük a Unique Constraint hibát, ha a kód már létezik más tábla alatt
        existing_nodes = {node.code: node for node in UniclassNode.objects.all()}

        new_objects = []
        update_objects = []

        # Segédhalmaz a duplikációk kiszűrésére az Excelen belül
        processed_codes_in_this_run = set()

        # 2. LÉPÉS: ADATOK FELDOLGOZÁSA
        for row in excel_rows:
            code = row[0]  # A oszlop: Kód

            # Ha az Excelben kétszer szerepel ugyanaz a kód, a másodikat átugorjuk
            if code in processed_codes_in_this_run:
                continue
            processed_codes_in_this_run.add(code)

            # CÍM (Title): G oszlop (index 6) az elsődleges, tartalék a B (index 1)
            title = row[6] if row[6] else row[1]

            desc = row[2]  # C: Leírás
            version = row[3]  # D: Verzió
            date = row[4]  # E: Dátum

            # Extrák (kivéve G)
            extras = " | ".join([r for i, r in enumerate(row[5:]) if r and i != 1])

            if code in existing_nodes:
                # FRISSÍTÉS
                node = existing_nodes[code]
                changed = False

                # Ha még nincs mentve (mert most hoztuk létre ebben a futásban), akkor a memóriában frissítjük
                # Ha már van ID-ja (adatbázisban volt), akkor update listába tesszük

                if node.title_en != title: node.title_en = title; changed = True
                if node.description != desc: node.description = desc; changed = True
                if node.version != version: node.version = version; changed = True
                if node.date != date: node.date = date; changed = True
                if node.extra_data != extras: node.extra_data = extras; changed = True

                # Csak akkor adjuk hozzá a bulk_update-hez, ha már létezik az DB-ben (van PK)
                if changed and node.pk:
                    update_objects.append(node)
            else:
                # LÉTREHOZÁS
                new_node = UniclassNode(
                    code=code,
                    title_en=title,
                    description=desc,
                    version=version,
                    date=date,
                    extra_data=extras,
                    table=table_code,
                    parent=None
                )
                new_objects.append(new_node)
                existing_nodes[code] = new_node  # Memóriába is betesszük

        # ADATBÁZIS MŰVELETEK
        if new_objects:
            self.stdout.write(f'{len(new_objects)} új elem mentése...')
            UniclassNode.objects.bulk_create(new_objects, batch_size=2000)

        if update_objects:
            # Egyedivé tesszük a listát (ha véletlenül többször került volna bele ugyanaz az objektum)
            unique_updates = list({obj.code: obj for obj in update_objects}.values())
            self.stdout.write(f'{len(unique_updates)} elem frissítése...')
            if unique_updates:
                UniclassNode.objects.bulk_update(unique_updates,
                                                 ['title_en', 'description', 'version', 'date', 'extra_data'],
                                                 batch_size=2000)

        # 3. LÉPÉS: HIERARCHIA (SZÜLŐK) ÉPÍTÉSE
        self.stdout.write('Hierarchia kapcsolatok építése...')

        # Újratöltjük a térképet, hogy a most létrehozottaknak is legyen ID-ja
        # Itt is mindenkit lekérünk, nem csak a táblát
        all_nodes_map = {node.code: node for node in UniclassNode.objects.all()}
        parent_updates = []

        for code in processed_codes_in_this_run:
            current_node = all_nodes_map.get(code)
            if not current_node: continue

            parts = code.split('_')
            parent_node = None

            if len(parts) > 1:
                parent_code = "_".join(parts[:-1])
                parent_node = all_nodes_map.get(parent_code)

            if current_node.parent_id != (parent_node.id if parent_node else None):
                current_node.parent = parent_node
                parent_updates.append(current_node)

        if parent_updates:
            self.stdout.write(f'{len(parent_updates)} szülő-kapcsolat beállítása...')
            UniclassNode.objects.bulk_update(parent_updates, ['parent'], batch_size=2000)

        self.stdout.write(self.style.SUCCESS(f'KÉSZ! Importálás sikeres.'))