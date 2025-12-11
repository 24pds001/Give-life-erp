from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_bill_student_employees'),
    ]

    operations = [
        migrations.AddField(
            model_name='bill',
            name='advance_payment_type',
            field=models.CharField(blank=True, choices=[('UPI', 'UPI'), ('CASH', 'Cash'), ('ONLINE', 'Online'), ('CHEQUE', 'Cheque'), ('CARD', 'Card'), ('NEFT', 'NEFT/IMPS')], max_length=20, null=True),
        ),
    ]
