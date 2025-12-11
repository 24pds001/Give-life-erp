from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_billpayment'),
    ]

    operations = [
        migrations.RunSQL(
            # Drop the columns if they exist. Using a stored procedure or just ignoring error? 
            # MySQL 'ALTER TABLE ... DROP COLUMN ...' fails if column doesn't exist?
            # Usually yes. But we know they exist because of the error.
            sql="ALTER TABLE core_bill DROP COLUMN cash_amount, DROP COLUMN upi_amount;",
            reverse_sql="" # Cannot reverse easily without knowing type, but it's cleanup.
        ),
    ]
