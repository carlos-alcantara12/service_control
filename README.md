# ServiceFlow

[English](README.md) · [Português](README.pt-BR.md)

A web application for **service order management** in repair shops and maintenance businesses. ServiceFlow tracks equipment from intake to delivery, keeping assignments, estimates, approvals, repairs, payments, and history in one workflow.

## What it solves

Repair operations often spread customer information, deadlines, and approvals across spreadsheets and messages. ServiceFlow brings these records together in a single service order and applies business rules to critical actions.

## Core workflow

1. Register the customer and equipment, then open a service order.
2. Assign a technician.
3. Record the diagnosis and prepare a versioned estimate.
4. Record the customer's decision for the exact estimate version.
5. Start the repair after valid approval.
6. Record activities, parts, and tests.
7. Record payment and equipment delivery.
8. Create a linked return order when needed, preserving the original history.

## Main modules

| Module | Purpose |
| --- | --- |
| Dashboard | Overview of open, overdue, pending approval, and ready orders. |
| Customers and equipment | Registration and service history. |
| Service orders | Intake, assignments, deadlines, diagnosis, repairs, tests, attachments, returns, and delivery. |
| Estimates | Items, amounts, versions, validity, and customer decisions. |
| Finance | Payments, outstanding balances, refunds, and cancellations. |
| Reports | Operational and financial indicators. |
| Users and audit | Role permissions and change history. |

## Business controls

- Unique, immutable service order numbers.
- Estimate approvals tied to a specific version.
- Controlled status transitions and backend monetary validation.
- Separate operational and financial status.
- Refunds limited to the amount actually paid.
- Delivery requires settlement unless a manager authorizes an exception.
- History preservation and access checks for managers, attendants, and technicians.

## Technology and architecture

- **Backend:** Python, Django, and Django REST Framework.
- **Frontend:** HTML, CSS, and modular JavaScript.
- **Database:** SQLite for development; PostgreSQL through `DATABASE_URL`.
- **Authentication:** Django sessions with CSRF protection.
- **Architecture:** frontend and API served by the same Django project; transactional services centralize critical business operations.

## Local setup

Python 3.11 or newer is recommended. From the repository root, in PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py check
python manage.py createsuperuser
python manage.py runserver
```

Open [http://localhost:8000/](http://localhost:8000/) and sign in. Django Admin is available at `/admin/`.

On Linux or macOS, use `python3 -m venv .venv` and `source .venv/bin/activate` for the environment setup.

## Configuration

| Variable | Purpose |
| --- | --- |
| `DJANGO_SECRET_KEY` | Application secret; configure a secure value for real deployments. |
| `DJANGO_DEBUG` | Debug mode; use `0` in production. |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated allowed hosts. |
| `DATABASE_URL` | PostgreSQL connection URL. |

## API and tests

The API is under `/api/` and uses session authentication. Resources cover customers, equipment, orders, estimates, payments, deliveries, and reports. Endpoint identifiers remain in Portuguese.

Run backend tests from `backend/`:

```powershell
python manage.py test
```

## Current scope

The MVP covers internal repair operations. Customer communication uses the business's existing channels; the application records decisions and evidence.

Commercial expansion requires additional work such as company-level data isolation, automated backups, production hosting, monitoring, notifications, customer portals, and external integrations.

## Documentation

- [Complete project reference in Portuguese](README.pt-BR.md)
- [Technical specification](docs/tech_spec)
- [Backend documentation](backend/README.md)
- [Frontend documentation](frontend/README.md)
