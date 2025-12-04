from decimal import Decimal
from datetime import date

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
import importlib

from .models import Employee, Attendance, PayrollItem, PublicHoliday


class HRViewsTest(TestCase):
    def setUp(self):
        # Fixált hónap a teszthez: aktuális hónap első napja
        today = timezone.now().date()
        self.year = today.year
        self.month = today.month
        self.month_str = today.strftime('%Y-%m')

        # Alap entitások
        self.emp1 = Employee.objects.create(name="Teszt Elek", position="Kőműves", daily_cost=Decimal('20000'), status='ACTIVE')
        self.emp2 = Employee.objects.create(name="Másik Béla", position="Segéd", daily_cost=Decimal('16000'), status='ACTIVE')

        # Bejelentkezett felhasználó szükséges a @login_required nézetekhez
        self.user = User.objects.create_user(username='tester', password='pw12345')
        self.client.force_login(self.user)

    def test_hr_calendar_context_has_header_days_and_today(self):
        # Ünnepnap a hónap 1. napjára (ha az ma nem 1, nem gond)
        PublicHoliday.objects.create(date=date(self.year, self.month, 1), name="Nemzeti Ünnep", is_workday=False)

        # Egyszerű jelenlét az emp1-nek a 2. napra
        Attendance.objects.create(employee=self.emp1, date=date(self.year, self.month, 2), status='WORK', hours_worked=Decimal('8.0'))

        url = reverse('hr-calendar') + f'?month={self.month_str}'
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertIn('header_days', resp.context)
        self.assertIn('calendar_data', resp.context)
        self.assertIn('is_current_month', resp.context)
        self.assertIn('today_day', resp.context)

        header_days = resp.context['header_days']
        # Ellenőrizze, hogy az 1. nap szerepel és ünnepnek jelölt
        one = [d for d in header_days if d['day'] == 1]
        self.assertTrue(one, "Az 1. napnak szerepelnie kell a fejlécben")
        self.assertTrue(one[0]['is_holiday'], "Az 1. nap ünnepnek kell legyen jelölve")

        # Ellenőrizzük, hogy az emp1 sorában a 2. naphoz tartozik attendance
        calendar_data = resp.context['calendar_data']
        row = next((r for r in calendar_data if r['employee'].id == self.emp1.id), None)
        self.assertIsNotNone(row)
        day2 = row['days'][1]  # index 1 -> 2. nap
        self.assertEqual(day2['status'], 'WORK')
        self.assertEqual(Decimal(day2['hours']), Decimal('8.0'))

    def test_hr_payroll_filters_and_totals(self):
        # Tétel hozzáadások különböző típusokkal
        PayrollItem.objects.create(employee=self.emp1, date=date(self.year, self.month, 3), type='ADVANCE', amount=Decimal('10000'), approved=True)
        PayrollItem.objects.create(employee=self.emp1, date=date(self.year, self.month, 5), type='PREMIUM', amount=Decimal('5000'), approved=False)
        PayrollItem.objects.create(employee=self.emp2, date=date(self.year, self.month, 7), type='DEDUCTION', amount=Decimal('3000'), approved=True)
        PayrollItem.objects.create(employee=self.emp2, date=date(self.year, self.month, 8), type='LOAN', amount=Decimal('2000'), approved=True)

        url = reverse('hr-payroll') + f'?month={self.month_str}'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        totals = resp.context['totals']
        self.assertEqual(totals['ADVANCE'], Decimal('10000'))
        self.assertEqual(totals['PREMIUM'], Decimal('5000'))
        self.assertEqual(totals['DEDUCTION'], Decimal('3000'))
        self.assertEqual(totals['LOAN'], Decimal('2000'))
        self.assertEqual(totals['NET'], Decimal('5000') - Decimal('10000') - Decimal('3000') - Decimal('2000'))

        # Szűrés dolgozóra
        url_emp1 = reverse('hr-payroll') + f'?month={self.month_str}&employee={self.emp1.id}'
        resp_emp1 = self.client.get(url_emp1)
        self.assertEqual(resp_emp1.status_code, 200)
        items = list(resp_emp1.context['items'])
        self.assertTrue(all(it.employee_id == self.emp1.id for it in items))

    def test_hr_payroll_export_xlsx(self):
        PayrollItem.objects.create(employee=self.emp1, date=date(self.year, self.month, 10), type='ADVANCE', amount=Decimal('1234.56'), approved=False)

        url = reverse('hr-payroll-export-xlsx') + f'?month={self.month_str}'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        self.assertIn('attachment; filename=', resp['Content-Disposition'])

    def test_hr_payroll_export_pdf(self):
        # készítünk egy tételt, hogy legyen tartalom
        PayrollItem.objects.create(employee=self.emp1, date=date(self.year, self.month, 10), type='ADVANCE', amount=Decimal('1234.56'), approved=False)

        # Ellenőrizzük, hogy elérhető-e a xhtml2pdf
        try:
            importlib.import_module('xhtml2pdf')
            has_pisa = True
        except ImportError:
            has_pisa = False

        url = reverse('hr-payroll-export-pdf') + f'?month={self.month_str}'
        resp = self.client.get(url)

        if has_pisa:
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp['Content-Type'], 'application/pdf')
            self.assertIn('attachment; filename=', resp['Content-Disposition'])
        else:
            # Ha nincs telepítve, a view 501-et ad vissza
            self.assertEqual(resp.status_code, 501)
