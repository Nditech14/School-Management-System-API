# 🏫 School Management System API

A production-ready Django REST API for managing schools, students, academics, and users — built with **Clean Architecture**, **JWT Auth**, **Role-Based Access**, **Swagger Docs**, **Cloudinary**, and **PostgreSQL**.

---

## ✅ Features

| Feature | Details |
|---|---|
| **Auth** | Email-based login (case-insensitive), JWT access + refresh tokens |
| **Roles** | Admin, Teacher, Student, Parent |
| **Students** | Profile, Guardian, Class enrollment |
| **Academics** | Subjects, Grades (CA + Exam), Attendance |
| **Audit Trail** | DB log + rotating file log for every key action |
| **Swagger Docs** | `/api/docs/` — full interactive API explorer |
| **Cloudinary** | Profile photo uploads via Cloudinary |
| **PostgreSQL** | Connected via `nditech` user |
| **Error Handling** | Custom exception handler — structured JSON errors |
| **Logging** | Separate logs: `app.log`, `audit.log`, `security.log` |

---

## ⚡ Quick Start

### 1. Clone & Install

```bash
git clone <repo>
cd school_management
pip install -r requirements.txt
```

### 2. Configure Environment

Edit `.env`:

```env
SECRET_KEY=your-secret-key
DB_NAME=school_db
DB_USER=nditech
DB_PASSWORD=nditech
DB_HOST=localhost
DB_PORT=5432
CLOUDINARY_URL=cloudinary://<api_key>:<api_secret>@danksdxj8
```

### 3. Setup PostgreSQL Database

```bash
# In psql as superuser:
CREATE USER nditech WITH PASSWORD 'nditech';
CREATE DATABASE school_db OWNER nditech;
GRANT ALL PRIVILEGES ON DATABASE school_db TO nditech;
```

### 4. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create Superuser

```bash
python manage.py createsuperuser
# Enter email (not username), first name, last name, password
```

### 6. Run Server

```bash
python manage.py runserver
```

---

## 📚 API Documentation

| URL | Description |
|---|---|
| `http://localhost:8000/api/docs/` | Swagger UI |
| `http://localhost:8000/api/redoc/` | ReDoc |
| `http://localhost:8000/admin/` | Django Admin |

---

## 🔐 Authentication Flow

```
POST /api/v1/auth/register/     → Create account
POST /api/v1/auth/login/        → Get access + refresh tokens
POST /api/v1/auth/token/refresh/ → Refresh access token
POST /api/v1/auth/logout/       → Blacklist refresh token
```

**All other endpoints require:**
```
Authorization: Bearer <access_token>
```

---

## 👥 User Roles & Permissions

| Role | Permissions |
|---|---|
| `admin` | Full access to everything |
| `teacher` | Read/write students, grades, attendance, subjects |
| `student` | Read own profile and grades |
| `parent` | Read linked student data |

---

## 🗂️ API Endpoints (v1)

### Auth
```
POST   /api/v1/auth/register/
POST   /api/v1/auth/login/
POST   /api/v1/auth/logout/
POST   /api/v1/auth/token/refresh/
```

### Profile
```
GET    /api/v1/profile/
PUT    /api/v1/profile/
PATCH  /api/v1/profile/
POST   /api/v1/profile/change-password/
```

### Admin — Users
```
GET    /api/v1/admin/users/
POST   /api/v1/admin/users/
GET    /api/v1/admin/users/<id>/
PUT    /api/v1/admin/users/<id>/
PATCH  /api/v1/admin/users/<id>/
DELETE /api/v1/admin/users/<id>/
```

### Academic Sessions
```
GET    /api/v1/academic-sessions/
POST   /api/v1/academic-sessions/
GET    /api/v1/academic-sessions/<id>/
PUT    /api/v1/academic-sessions/<id>/
DELETE /api/v1/academic-sessions/<id>/
```

### Classrooms
```
GET    /api/v1/classrooms/
POST   /api/v1/classrooms/
GET    /api/v1/classrooms/<id>/
PUT    /api/v1/classrooms/<id>/
DELETE /api/v1/classrooms/<id>/
```

### Students
```
GET    /api/v1/students/
POST   /api/v1/students/
GET    /api/v1/students/<id>/
PUT    /api/v1/students/<id>/
PATCH  /api/v1/students/<id>/
DELETE /api/v1/students/<id>/
```

### Guardians
```
GET    /api/v1/guardians/
POST   /api/v1/guardians/
GET    /api/v1/guardians/<id>/
PUT    /api/v1/guardians/<id>/
```

### Subjects
```
GET    /api/v1/subjects/
POST   /api/v1/subjects/
GET    /api/v1/subjects/<id>/
PUT    /api/v1/subjects/<id>/
DELETE /api/v1/subjects/<id>/
```

### Grades
```
GET    /api/v1/grades/
POST   /api/v1/grades/
GET    /api/v1/grades/<id>/
PUT    /api/v1/grades/<id>/
DELETE /api/v1/grades/<id>/
```

### Attendance
```
GET    /api/v1/attendance/
POST   /api/v1/attendance/
GET    /api/v1/attendance/<id>/
PUT    /api/v1/attendance/<id>/
```

### Audit Trail (Admin only)
```
GET    /api/v1/audit-logs/
GET    /api/v1/audit-logs/<id>/
```

---

## 🗄️ Project Structure

```
school_management/
├── config/                  # Django project config
│   ├── settings.py          # All settings
│   └── urls.py              # Root URL routing (API v1)
│
├── core/                    # Shared utilities (Clean Architecture)
│   ├── exceptions.py        # Custom DRF exception handler
│   ├── middleware.py        # Request logging middleware
│   ├── pagination.py        # Standard paginator
│   ├── permissions.py       # Role-based permission classes
│   └── responses.py         # APIResponse factory
│
├── users/                   # Auth & User management
│   ├── models.py            # Custom User (email login, roles)
│   ├── serializers.py       # Registration, Profile, JWT
│   ├── views.py             # Auth, Profile, Admin CRUD
│   └── urls.py
│
├── students/                # Student domain
│   ├── models.py            # StudentProfile, Guardian, ClassRoom, AcademicSession
│   ├── serializers.py       # ModelSerializer + Serializer
│   ├── views.py             # Full CRUD views
│   └── urls.py
│
├── academics/               # Academic records
│   ├── models.py            # Subject, Grade, Attendance
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
│
├── audit_trail/             # Audit & logging
│   ├── models.py            # AuditLog
│   ├── serializers.py
│   ├── views.py             # Read-only admin views
│   ├── utils.py             # log_action() helper
│   └── urls.py
│
├── logs/                    # Auto-created at runtime
│   ├── app.log
│   ├── audit.log
│   └── security.log
│
├── .env                     # Environment variables
├── requirements.txt
└── manage.py
```

---

## 🧩 Serializer Patterns Used

| Pattern | Where Used |
|---|---|
| `serializers.Serializer` | `ChangePasswordSerializer`, `CustomTokenObtainPairSerializer` |
| `serializers.ModelSerializer` | All model serializers (`UserProfileSerializer`, `StudentProfileSerializer`, etc.) |
| `SerializerMethodField` | Computed fields: `full_name`, `age`, `class_name`, `student_count` |
| `write_only` fields | `password`, `password_confirm`, `old_password` |
| `read_only_fields` | `id`, timestamps, auto-computed fields |
| Nested serializers | `user_info` inside `StudentProfileSerializer` |

---

## 📝 Logging Files

| File | Contents |
|---|---|
| `logs/app.log` | All Django + API request/response logs |
| `logs/audit.log` | Business-level audit events (CRUD, login/logout) |
| `logs/security.log` | Auth failures, password changes, suspicious activity |

---

## ☁️ Cloudinary Setup

Replace in `.env`:
```
CLOUDINARY_URL=cloudinary://<your_api_key>:<your_api_secret>@danksdxj8
```

All `ImageField` uploads (profile photos) go directly to Cloudinary via `django-cloudinary-storage`.

---

## 🛡️ Error Response Format

All errors return:
```json
{
  "success": false,
  "status_code": 400,
  "message": "Validation failed. Please check the submitted data.",
  "errors": {
    "email": ["Enter a valid email address."],
    "password": ["This password is too short."]
  }
}
```

## ✅ Success Response Format

```json
{
  "success": true,
  "message": "Student registered successfully.",
  "data": { ... }
}
```

Paginated lists:
```json
{
  "success": true,
  "count": 100,
  "total_pages": 5,
  "current_page": 1,
  "next": "http://localhost:8000/api/v1/students/?page=2",
  "previous": null,
  "results": [ ... ]
}
```
