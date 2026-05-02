# Northshore Logistics Ltd – Database System
## CPS4004 Database Systems – Assessment 2

### Overview
A centralised database management system for Northshore Logistics Ltd,
built with Python 3.11+, SQLite 3, and Tkinter.

---

### Quick Start

1. **Install Python 3.11+** (Tkinter is bundled with standard Python)

2. **Clone or extract** the project folder

3. **Navigate** to the project root:
   ```
   cd northshore
   ```

4. **Seed sample data** (recommended for first run):
   ```
   python src/seed_data.py
   ```

5. **Run the application**:
   ```
   python src/app.py
   ```

---

### Default Login Credentials

| Username   | Password    | Role      |
|------------|-------------|-----------|
| admin      | admin123    | Admin     |
| manager1   | manager123  | Manager   |
| warehouse1 | wh123456    | Warehouse |
| driver1    | driver123   | Driver    |

> **Note:** Change the default admin password immediately in a real deployment.

---

### Project Structure

```
northshore/
├── src/
│   ├── app.py          # Main Tkinter GUI application
│   ├── database.py     # SQLite schema, security helpers, audit logging
│   ├── auth.py         # Authentication and RBAC session management
│   └── seed_data.py    # Sample data generator (run once)
├── northshore.db       # SQLite database (auto-created on first run)
├── northshore_audit.log# Audit trail (auto-created)
└── README.md
```

---

### Features

- **Shipment Management** – Add, update, track, and report on shipments
- **Inventory Management** – Stock levels with low-stock alerts
- **Fleet Management** – Vehicle tracking and maintenance scheduling
- **Driver Profiles** – License records with encrypted PII
- **Customer Directory** – Encrypted addresses and contact details
- **Incident Reporting** – Track delays, damage, and resolutions
- **Operational Reports** – Status breakdowns, financials, warehouse activity
- **Role-Based Access Control** – Admin / Manager / Warehouse / Driver roles
- **Data Encryption** – Sensitive fields (addresses, licenses, phone numbers) obfuscated
- **Audit Logging** – Every INSERT/UPDATE recorded with user and timestamp

---

### Security Notes

- Passwords are stored as `salt$sha256(salt+password)` – never in plain text
- Sensitive PII fields use XOR obfuscation at rest
- All database write operations are recorded in the audit log
- Role-based permissions restrict screen/feature access per user role

---

### No External Dependencies

Only Python standard library modules are used:
- `sqlite3` – database
- `tkinter` – GUI
- `hashlib` – password hashing
- `secrets` – salt generation
- `logging` – file-based audit trail
- `datetime` – timestamps
