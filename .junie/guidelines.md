Construction ERP – Development Guidelines (Project‑Specific)

Audience: Experienced Django developers working on this repository.

1) Build and Configuration
- Python/venv: Project runs on Python 3.11 (see pip output path) with Django 5.2.8 (settings header). Use a dedicated venv.
  - python -m venv venv
  - venv\Scripts\activate
  - pip install "Django==5.2.8"
  No requirements.txt is present; install any additional libs as you introduce them.

- Settings highlights: construction_erp/settings.py
  - LANGUAGE_CODE = 'hu' and USE_THOUSAND_SEPARATOR = True. Humanize is enabled (django.contrib.humanize); templates use intcomma. Keep locale-aware formatting in mind.
  - Database: SQLite (db.sqlite3 by default). No custom routers.
  - Media: MEDIA_URL = '/media/' and MEDIA_ROOT = BASE_DIR / 'media'. In DEBUG, URLs are served via construction_erp/urls.py using static(). Avoid relying on this for production.
  - INSTALLED_APPS includes: projects (primary domain app) and the usual Django contrib apps.

- URLs
  - Root routes to projects.urls. Add new app URLs by including them here or inside projects as needed.
  - Media route addition is guarded by settings.DEBUG.

- Migrations
  - Generate/apply as standard:
    - python manage.py makemigrations
    - python manage.py migrate
  - The projects app has existing migrations, including model option changes and new fields (e.g., Tetelsor editable fields reintroduced). Ensure any model edits maintain forward/backward compatibility.

- Admin
  - Admin site is enabled at /admin/. If adding models, register them and use createsuperuser for local inspection.

2) Testing: How to configure and run
- Runner: Standard Django test runner. No pytest config in repo; use python manage.py test.
- Discovery: Django will auto-discover tests in files matching test*.py within app packages (e.g., projects/tests.py or projects/test_*.py). Current placeholder tests.py files exist in multiple apps; they do not assert anything.
- Database: Each TestCase uses a temporary test DB (SQLite). Rely on Django TestCase transactional behavior for isolation.
- Running tests:
  - venv\Scripts\activate
  - python manage.py test
- Adding tests:
  - Create test modules under the corresponding app (e.g., projects/test_tetelsor_logic.py). Use django.test.TestCase.
  - Prefer Decimal for monetary values and time-based metrics to avoid float issues, consistent with models.

- Sample test (validated locally)
  The following test exercises Tetelsor save() computations that are specific to this project. It created and passed during validation; include similar logic in your permanent tests as needed.

  from decimal import Decimal
  from django.test import TestCase
  from projects.models import Project, Material, MasterItem, Tetelsor

  class TetelsorComputationTest(TestCase):
      def test_tetelsor_computed_fields(self):
          project = Project.objects.create(name="Test Project", location="Budapest")
          mat = Material.objects.create(name="Cement", unit="kg", price=Decimal("250.00"))
          master = MasterItem.objects.create(
              tetelszam="T-0001", leiras="Teszt tétel", egyseg="m2",
              normaido=Decimal("0.00"), fix_anyag_ar=Decimal("0.00")
          )
          ts = Tetelsor.objects.create(
              project=project, master_item=master, leiras="Szerk.", egyseg="m2",
              normaido=Decimal("2.00"), mennyiseg=Decimal("3.00"),
              labor_split_percentage=Decimal("60.00"), material=mat,
          )
          ts.refresh_from_db()
          self.assertEqual(ts.anyag_egysegar, Decimal("250.00"))
          self.assertEqual(ts.anyag_osszesen, Decimal("750.00"))
          self.assertEqual(ts.dij_egysegre_sajat, Decimal("6000.00"))
          self.assertEqual(ts.dij_egysegre_alv, Decimal("4000.00"))
          self.assertEqual(ts.sajat_munkadij_osszesen, Decimal("18000.00"))
          self.assertEqual(ts.alv_munkadij_osszesen, Decimal("12000.00"))

3) Project-Specific Development Notes
- Monetary/quantities and precision
  - Use Decimal fields throughout. Avoid float arithmetic in views/forms; cast to Decimal when needed.
  - Templates often apply intcomma and floatformat; with LANGUAGE_CODE='hu' and USE_THOUSAND_SEPARATOR=True, separators are locale-aware.

- Tetelsor business logic (projects.models.Tetelsor.save)
  - anyag_egysegar selection:
    - If material is set and has price: use that price.
    - Else if not set and master_item exists: fallback to master_item.calculated_material_cost.
  - Computations per save():
    - anyag_osszesen = mennyiseg * anyag_egysegar
    - full_labor = project.hourly_rate * normaido
    - dij_egysegre_sajat = full_labor * (labor_split_percentage/100)
    - dij_egysegre_alv = full_labor * (1 - labor_split_percentage/100)
    - sajat_munkadij_osszesen = mennyiseg * dij_egysegre_sajat
    - alv_munkadij_osszesen = mennyiseg * dij_egysegre_alv
  - Ensure callers update normaido, mennyiseg, labor_split_percentage, material consistently before save().
  - The tetelszam exposed on Tetelsor is a proxy from master_item.tetelszam (property), not a DB column.
  - Unique constraint: (project, master_item). Handle IntegrityError when bulk-adding the same master item to a project.

- MasterItem.calculated_material_cost
  - Sums ItemComponent.amount * Material.price over related components when present; otherwise falls back to fix_anyag_ar. Ensure components are prefetched when listing many rows to avoid N+1.

- DailyLog
  - date is globally unique (not per project). This may be intentional for a single active project per day; otherwise consider making it unique_for_date within project or a UniqueConstraint on (project, date). Be mindful when importing historical logs.

- Expense
  - invoice_file stored in MEDIA_ROOT/invoices/. In DEBUG, files are served via URLs configured in construction_erp/urls.py. For production, serve media via web server and disable DEBUG.

- Templates and localization
  - The UI and labels are Hungarian. Keep terminology consistent. Existing templates use humanize and localized dates. When adding templates, include {% load humanize %} where intcomma is used.

- Performance tips
  - Use select_related for foreign keys commonly displayed together (e.g., Tetelsor.project, Tetelsor.master_item, Tetelsor.material, Tetelsor.munkanem) and prefetch_related for reverse M2O (e.g., master_item.components.select_related('material')).

- Admin/testing data
  - For quick data seeding in tests, prefer factories or lightweight ModelFactory functions if you add pytest/factory_boy later. For now, keep TestCase helpers under tests/.

4) Typical Dev Flows
- Spin up server: python manage.py runserver (ensure DB migrated). Create a superuser to access /admin/.
- Add a new model field impacting computed totals:
  - Update models with Decimal defaults, write a test covering save() logic, add a migration, verify list/detail template columns if relevant.
- Import/export or file uploads:
  - Keep MEDIA_ROOT path handling; do not hardcode absolute paths. Use request.build_absolute_uri for links in emails or exports.

5) Troubleshooting
- Formatting looks odd in templates for numbers:
  - Confirm django.contrib.humanize is in INSTALLED_APPS and {% load humanize %} is in the template, and USE_THOUSAND_SEPARATOR=True.
- Material cost not updating:
  - If Tetelsor.material is set, it overrides master_item.calculated_material_cost. Clear material to fallback to the master.
- Duplicate Tetelsor entries for the same master item in a project:
  - Check unique_together on (project, master_item). Catch and surface a clean validation error in forms.

This document intentionally focuses on project-specific behavior. Update it as domain logic evolves (especially Tetelsor computations, DailyLog uniqueness, and localization settings).
