# projects/management/commands/create_roles.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from projects.models import Project, DailyLog, ProjectDocument, Expense, MaterialOrder, Tetelsor


class Command(BaseCommand):
    help = 'Létrehozza az alapértelmezett szerepköröket (Építésvezető, Pénzügyes)'

    def handle(self, *args, **options):
        # 1. ÉPÍTÉSVEZETŐ CSOPORT
        site_mgr, created = Group.objects.get_or_create(name='Epitesvezeto')

        # Jogosultságok gyűjtése
        models_for_site = [Project, DailyLog, ProjectDocument]
        perms_for_site = []

        for model in models_for_site:
            ct = ContentType.objects.get_for_model(model)
            # Hozzáadás, Módosítás, Megtekintés (Törlés NEM!)
            p = Permission.objects.filter(content_type=ct, codename__in=[
                f'add_{model._meta.model_name}',
                f'change_{model._meta.model_name}',
                f'view_{model._meta.model_name}'
            ])
            perms_for_site.extend(p)

        site_mgr.permissions.set(perms_for_site)
        self.stdout.write(self.style.SUCCESS('Sikeresen létrehozva: Epitesvezeto (Csak szakmai adatok)'))

        # 2. PÉNZÜGYES CSOPORT
        finance, created = Group.objects.get_or_create(name='Penzugyes')

        models_for_finance = [Project, Expense, MaterialOrder, Tetelsor]
        perms_for_finance = []

        for model in models_for_finance:
            ct = ContentType.objects.get_for_model(model)
            # Minden jog (Törlés is) a pénzügyi dolgokhoz
            p = Permission.objects.filter(content_type=ct)
            perms_for_finance.extend(p)

        finance.permissions.set(perms_for_finance)
        self.stdout.write(self.style.SUCCESS('Sikeresen létrehozva: Penzugyes (Pénzügyi adatok)'))