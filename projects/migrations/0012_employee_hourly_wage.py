 # Merge migration to resolve conflict between 0004 and 0011
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0011_alter_tetelsor_unique_together"),
        ("projects", "0004_employee_hourly_wage"),
    ]

    # No operations: this file now only merges the two branches.
    operations = []
