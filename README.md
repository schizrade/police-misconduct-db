# Police Misconduct Database — Enhanced Version 2.0

A comprehensive web application for tracking and analyzing police misconduct incidents with **authentication**, **CSV import**, and **file upload** capabilities.

## 🆕 New Features in V2.0

- ✅ Secure login system with JWT tokens
- ✅ Role-based access control (Admin, Data Entry, Reviewer, Viewer)
- ✅ Bulk import incidents / officers / departments from CSV or Excel
- ✅ Upload evidence files (PDF, images, videos, documents) linked to incidents
- ✅ Workflow system: `draft → review → verified → published`
- ✅ Full audit trail on all data changes

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI + uvicorn |
| Database | PostgreSQL 14+ |
| ORM | SQLAlchemy 2 |
| Auth | JWT (python-jose) + bcrypt |
| CSV/Excel | pandas + openpyxl |
| Frontend | React 18 + Chart.js |
| Web server | Nginx |
| OS | Ubuntu 22.04 / 24.04 LTS |

## Quick Start

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/police-misconduct-db.git
cd police-misconduct-db

# Run the one-command setup (Ubuntu 22.04/24.04, requires sudo)
sudo bash setup.sh
```

See **[QUICKSTART.md](QUICKSTART.md)** for full dependency list, post-install steps, SSL setup, and troubleshooting.

## Default Admin Account

| Field | Value |
|---|---|
| Username | `admin` |
| Password | `admin123` |

> ⚠️ **Change this immediately after first login.**

## API Documentation

After installation, Swagger UI is available at:
```
http://your-server-ip/api/docs
```

## User Roles

| Role | Permissions |
|---|---|
| **Admin** | Full access — manage users, all CRUD, all data |
| **Data Entry** | Create/edit incidents, upload files, import CSVs |
| **Reviewer** | Approve incidents, change workflow status |
| **Viewer** | View published public incidents only |

## License

Open source — use responsibly for public transparency and accountability.
