# Shop System (Django)

This repository contains a minimal Django-based shop management web app with:
- Custom `User` model with roles (Admin, Accountant, Supervisor, Employee)
- Item management (CRUD)
- Billing (Inner, Outer, Sales) with printable invoices
- Inventory tracking and auto-generated sales bills from inventory returns
- Role-based permissions: Admin has full control; Supervisors have broader access; Employees limited to their own bills

Prerequisites
- Python 3.10+ (use your project's venv)
- MySQL server

Setup (PowerShell)

1. Create and activate a virtual environment
```
python -m venv .venv; .\.venv\Scripts\Activate.ps1
```

2. Install dependencies
```
pip install -r requirements.txt
```

3. Configure MySQL
- Create a database and user (example):
```
mysql -u root -p;
CREATE DATABASE shop_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'shop_user'@'localhost' IDENTIFIED BY 'strong_password';
GRANT ALL ON shop_db.* TO 'shop_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```
- Update `shop_system/settings.py` DATABASES section to use the credentials above (`NAME`, `USER`, `PASSWORD`).

4. Apply migrations and create a superuser
```
python manage.py migrate
python manage.py createsuperuser
```

5. Run the development server
```
python manage.py runserver
```

Notes
- Default DB in `shop_system/settings.py` is configured for `shop_db` with `root`/`root` placeholders — change before running in your environment.
- Templates are in `core/templates/core/`. Use the admin site (`/admin/`) for direct model access.

If you want, I can:
- Add password-change links in the UI (I already added URL routes and templates),
- Add sample data fixtures, or
- Harden the deployment settings for production.
