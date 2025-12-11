from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_bill_advance_payment_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='BillPayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payment_type', models.CharField(choices=[('UPI', 'UPI'), ('CASH', 'Cash'), ('ONLINE', 'Online'), ('CHEQUE', 'Cheque'), ('CARD', 'Card'), ('NEFT', 'NEFT/IMPS')], max_length=20)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('reference_number', models.CharField(blank=True, max_length=50)),
                ('bill', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='core.bill')),
            ],
        ),
    ]
