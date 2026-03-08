# InvoiceHub 🚀
### Invoice Automation Web App for Indian Small Businesses

A production-ready Flask application for coaching classes and gyms to manage clients, generate GST-compliant invoices, automate email delivery, and track payments.

---

## ✨ Features

- **Admin Authentication** — Secure login with hashed passwords
- **Client Management** — Full CRUD: add, edit, delete, view clients
- **GST Invoices** — 18% GST calculation, unique invoice numbers
- **PDF Generation** — Professional PDFs with embedded UPI QR code via ReportLab
- **Email Automation** — Auto-send invoice + PDF on creation via SMTP
- **Payment Tracking** — Mark paid/unpaid, record payment date
- **Overdue Reminders** — Daily background job sends reminder emails
- **Dashboard** — Revenue charts, stats, recent invoices (Chart.js)
- **Recurring Invoices** — Monthly auto-generation for all active clients
- **CSV Export** — Download all invoices as spreadsheet
- **Responsive UI** — Clean dark sidebar, mobile-friendly

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, Flask, SQLAlchemy |
| Database | PostgreSQL (prod) / SQLite (dev) |
| Frontend | Bootstrap 5, Jinja2, Chart.js |
| PDF | ReportLab + qrcode |
| Email | smtplib (Gmail SMTP) |
| Scheduler | APScheduler |
| Deploy | Gunicorn, Render/Railway |

---

## 🚀 Quick Start (Local Development)

### 1. Clone & Install

```bash
git clone <your-repo>
cd invoice_app
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

Minimum required settings in `.env`:
```env
SECRET_KEY=your-random-secret-key
COMPANY_NAME=My Coaching Classes
UPI_ID=yourname@upi
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=YourPassword@123
```

### 3. Run

```bash
python app.py
```

Visit: http://localhost:5000

**Default Login:**
- Email: `admin@example.com` (or your ADMIN_EMAIL)
- Password: `Admin@123` (or your ADMIN_PASSWORD)

---

## 📧 Email Configuration (Gmail)

1. Enable 2-Step Verification on your Gmail
2. Go to Google Account → Security → App Passwords
3. Generate an App Password for "Mail"
4. Use it in `.env`:

```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-gmail@gmail.com
MAIL_PASSWORD=your-16-char-app-password
MAIL_DEFAULT_SENDER=your-gmail@gmail.com
```

---

## ☁️ Deploy on Render (Free)

### Option 1: Using render.yaml (Recommended)

1. Push code to GitHub
2. Go to [render.com](https://render.com) → New → Blueprint
3. Connect your GitHub repo
4. Render auto-detects `render.yaml` and creates web service + PostgreSQL
5. Add environment variables in Render dashboard:
   - `COMPANY_NAME`, `COMPANY_ADDRESS`, `COMPANY_PHONE`, `COMPANY_EMAIL`
   - `COMPANY_GSTIN`, `UPI_ID`
   - `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER`
   - `ADMIN_EMAIL`, `ADMIN_PASSWORD`
   - `APP_URL` (your render URL, e.g. `https://invoicehub.onrender.com`)

### Option 2: Manual Deploy

1. New → Web Service → Connect GitHub repo
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `gunicorn app:app --workers 2 --bind 0.0.0.0:$PORT`
4. Add PostgreSQL database from Render dashboard
5. Set `DATABASE_URL` env var to the PostgreSQL connection string

---

## 🚂 Deploy on Railway

```bash
# Install Railway CLI
npm install -g @railway/cli
railway login
railway init
railway add postgresql
railway up
```

Set environment variables in Railway dashboard.

---

## 📁 Project Structure

```
invoice_app/
├── app.py                    # Application factory & entry point
├── config.py                 # Configuration (dev/prod)
├── models.py                 # SQLAlchemy models (Admin, Client, Invoice)
├── routes/
│   ├── auth.py               # Login / logout
│   ├── dashboard.py          # Dashboard + chart API
│   ├── clients.py            # Client CRUD
│   └── invoices.py           # Invoice CRUD, PDF, email, CSV
├── templates/
│   ├── base.html             # Base layout with sidebar
│   ├── auth/login.html
│   ├── dashboard/index.html
│   ├── clients/{index,form,view}.html
│   └── invoices/{index,form,view}.html
├── static/
│   ├── css/style.css
│   └── js/app.js
├── utils/
│   ├── pdf_generator.py      # ReportLab PDF + QR code
│   ├── email_sender.py       # SMTP email functions
│   └── scheduler.py          # APScheduler background jobs
├── invoices/                 # Generated PDF files (gitignored)
├── requirements.txt
├── .env.example
├── Procfile                  # For Heroku/Render
├── render.yaml               # Render deploy config
└── README.md
```

---

## 🔒 Security Notes

- Passwords are hashed with Werkzeug's `generate_password_hash` (PBKDF2)
- Sessions secured with `SECRET_KEY`
- All routes protected with `@login_required`
- Form validation on all inputs
- SQL injection prevented via SQLAlchemy ORM

---

## 📝 Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | ✅ | Flask session secret |
| `DATABASE_URL` | For prod | PostgreSQL URL |
| `COMPANY_NAME` | ✅ | Your business name |
| `COMPANY_ADDRESS` | ✅ | Full address |
| `COMPANY_PHONE` | ✅ | Contact number |
| `COMPANY_EMAIL` | ✅ | Business email |
| `COMPANY_GSTIN` | Optional | Your GSTIN |
| `UPI_ID` | ✅ | UPI ID for QR code |
| `MAIL_USERNAME` | For email | Gmail address |
| `MAIL_PASSWORD` | For email | Gmail App Password |
| `ADMIN_EMAIL` | ✅ | First admin email |
| `ADMIN_PASSWORD` | ✅ | First admin password |
| `APP_URL` | For email links | Your app's public URL |

---

## 📄 License

MIT License. Free to use for your business.
