from decimal import Decimal
from django.test import TestCase
from projects.models import Project, Supplier, Material, MasterItem, Tetelsor


class TetelsorComputationTest(TestCase):
    def test_tetelsor_computed_fields(self):
        # Base project (uses default hourly_rate=5000 Ft/h)
        project = Project.objects.create(
            name="Test Project",
            location="Budapest",
        )

        # Material with a defined unit price
        mat = Material.objects.create(
            name="Cement",
            unit="kg",
            price=Decimal("250.00"),
        )

        # Minimal master item (tetelszam is key here)
        master = MasterItem.objects.create(
            tetelszam="T-0001",
            leiras="Teszt tétel",
            egyseg="m2",
            normaido=Decimal("0.00"),
            fix_anyag_ar=Decimal("0.00"),
        )

        # Create Tetelsor that references the material and overrides editable fields
        ts = Tetelsor.objects.create(
            project=project,
            master_item=master,
            leiras="Szerkeszthető leírás",
            egyseg="m2",
            normaido=Decimal("2.00"),
            mennyiseg=Decimal("3.00"),
            labor_split_percentage=Decimal("60.00"),  # 60% own labor, 40% subcontractor
            material=mat,
        )

        # Refresh from DB to ensure computed fields persisted
        ts.refresh_from_db()

        # Expected computations
        # Material
        self.assertEqual(ts.anyag_egysegar, Decimal("250.00"))
        self.assertEqual(ts.anyag_osszesen, Decimal("750.00"))  # 3 * 250

        # Labor split calculations
        rate = Decimal("5000.00")  # from Project default hourly_rate
        full_labor = rate * Decimal("2.00")  # normaido
        self.assertEqual(full_labor, Decimal("10000.00"))

        self.assertEqual(ts.dij_egysegre_sajat, Decimal("6000.00"))  # 10000 * 0.6
        self.assertEqual(ts.dij_egysegre_alv, Decimal("4000.00"))    # 10000 * 0.4

        # Totals per quantity (mennyiseg=3)
        self.assertEqual(ts.sajat_munkadij_osszesen, Decimal("18000.00"))
        self.assertEqual(ts.alv_munkadij_osszesen, Decimal("12000.00"))
