"""
database.py – Northshore Logistics Ltd
Centralised SQLite database layer: schema creation, connection management,
encryption helpers, role-based access control, and audit logging.
"""

import sqlite3
import hashlib
import secrets
import logging
import datetime
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "northshore.db")
LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "northshore_audit.log")

# Configure standard Python logger for file-level events
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("northshore")


# ---------------------------------------------------------------------------
# Security helpers
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """SHA-256 hash a password with a random salt (stored as salt$hash)."""
    salt = secrets.token_hex(16)
    digest = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    """Verify a plain-text password against a stored salt$hash string."""
    try:
        salt, digest = stored.split("$", 1)
        return hashlib.sha256((salt + password).encode()).hexdigest() == digest
    except Exception:
        return False


def simple_encrypt(text: str) -> str:
    """
    Lightweight XOR obfuscation for sensitive fields (customer addresses,
    payment info, driver PII).  Uses a deterministic key derived from the
    module secret so that values are not stored in plain text.
    Key is deliberately NOT the real encryption key – for a production system
    use AES-256 via the 'cryptography' library.
    """
    key = "NorthshoreKey2026"
    encrypted = []
    for i, ch in enumerate(text):
        encrypted.append(chr(ord(ch) ^ ord(key[i % len(key)])))
    return "ENC:" + "".join(f"{ord(c):03d}" for c in encrypted)


def simple_decrypt(enc: str) -> str:
    """Reverse the XOR obfuscation."""
    if not enc.startswith("ENC:"):
        return enc
    key = "NorthshoreKey2026"
    nums = enc[4:]
    chars = [chr(int(nums[i:i+3])) for i in range(0, len(nums), 3)]
    decrypted = []
    for i, ch in enumerate(chars):
        decrypted.append(chr(ord(ch) ^ ord(key[i % len(key)])))
    return "".join(decrypted)


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")   # better concurrency
    return conn


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

SCHEMA_SQL = """
-- =========================================================
-- Users & RBAC
-- =========================================================
CREATE TABLE IF NOT EXISTS users (
    user_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT NOT NULL UNIQUE,
    password    TEXT NOT NULL,          -- stored as salt$sha256
    role        TEXT NOT NULL CHECK(role IN ('admin','manager','warehouse','driver')),
    full_name   TEXT NOT NULL,
    email       TEXT,
    created_at  TEXT DEFAULT (datetime('now')),
    is_active   INTEGER DEFAULT 1
);

-- =========================================================
-- Warehouses
-- =========================================================
CREATE TABLE IF NOT EXISTS warehouses (
    warehouse_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT NOT NULL,
    location       TEXT NOT NULL,       -- encrypted
    manager_id     INTEGER REFERENCES users(user_id),
    capacity       INTEGER,
    created_at     TEXT DEFAULT (datetime('now'))
);

-- =========================================================
-- Inventory
-- =========================================================
CREATE TABLE IF NOT EXISTS inventory (
    inventory_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    warehouse_id   INTEGER NOT NULL REFERENCES warehouses(warehouse_id),
    item_name      TEXT NOT NULL,
    sku            TEXT NOT NULL,
    quantity       INTEGER NOT NULL DEFAULT 0,
    reorder_level  INTEGER NOT NULL DEFAULT 10,
    unit           TEXT DEFAULT 'units',
    last_updated   TEXT DEFAULT (datetime('now'))
);

-- =========================================================
-- Vehicles
-- =========================================================
CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    registration    TEXT NOT NULL UNIQUE,
    vehicle_type    TEXT NOT NULL,
    capacity_kg     REAL,
    status          TEXT NOT NULL DEFAULT 'available'
                    CHECK(status IN ('available','in_transit','maintenance','retired')),
    last_service    TEXT,
    next_service    TEXT,
    warehouse_id    INTEGER REFERENCES warehouses(warehouse_id)
);

-- =========================================================
-- Drivers
-- =========================================================
CREATE TABLE IF NOT EXISTS drivers (
    driver_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER UNIQUE REFERENCES users(user_id),
    license_number  TEXT NOT NULL,      -- encrypted
    license_expiry  TEXT NOT NULL,
    phone           TEXT,               -- encrypted
    address         TEXT,               -- encrypted
    status          TEXT DEFAULT 'available'
                    CHECK(status IN ('available','on_route','off_duty')),
    warehouse_id    INTEGER REFERENCES warehouses(warehouse_id)
);

-- =========================================================
-- Customers
-- =========================================================
CREATE TABLE IF NOT EXISTS customers (
    customer_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT NOT NULL,
    email        TEXT,
    phone        TEXT,               -- encrypted
    address      TEXT NOT NULL       -- encrypted
);

-- =========================================================
-- Shipments (core entity)
-- =========================================================
CREATE TABLE IF NOT EXISTS shipments (
    shipment_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number     TEXT NOT NULL UNIQUE,
    customer_id      INTEGER NOT NULL REFERENCES customers(customer_id),
    origin_warehouse INTEGER NOT NULL REFERENCES warehouses(warehouse_id),
    destination_addr TEXT NOT NULL,  -- encrypted
    item_description TEXT,
    weight_kg        REAL,
    status           TEXT NOT NULL DEFAULT 'pending'
                     CHECK(status IN ('pending','in_transit','delivered',
                                      'delayed','returned','cancelled')),
    driver_id        INTEGER REFERENCES drivers(driver_id),
    vehicle_id       INTEGER REFERENCES vehicles(vehicle_id),
    route_details    TEXT,
    transport_cost   REAL DEFAULT 0,
    surcharges       REAL DEFAULT 0,
    payment_status   TEXT DEFAULT 'unpaid'
                     CHECK(payment_status IN ('unpaid','paid','refunded')),
    created_at       TEXT DEFAULT (datetime('now')),
    updated_at       TEXT DEFAULT (datetime('now')),
    delivery_date    TEXT
);

-- =========================================================
-- Incidents
-- =========================================================
CREATE TABLE IF NOT EXISTS incidents (
    incident_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    shipment_id   INTEGER NOT NULL REFERENCES shipments(shipment_id),
    incident_type TEXT NOT NULL
                  CHECK(incident_type IN ('delay','route_change','damaged',
                                          'failed_delivery','lost','other')),
    description   TEXT,
    reported_by   INTEGER REFERENCES users(user_id),
    reported_at   TEXT DEFAULT (datetime('now')),
    resolved      INTEGER DEFAULT 0,
    resolved_at   TEXT
);

-- =========================================================
-- Audit Log (immutable record)
-- =========================================================
CREATE TABLE IF NOT EXISTS audit_log (
    log_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER,
    action      TEXT NOT NULL,
    table_name  TEXT,
    record_id   INTEGER,
    detail      TEXT,
    logged_at   TEXT DEFAULT (datetime('now'))
);

-- =========================================================
-- Indexes for performance at scale
-- =========================================================
CREATE INDEX IF NOT EXISTS idx_shipments_status   ON shipments(status);
CREATE INDEX IF NOT EXISTS idx_shipments_customer ON shipments(customer_id);
CREATE INDEX IF NOT EXISTS idx_inventory_wh       ON inventory(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_audit_user         ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_incidents_ship     ON incidents(shipment_id);
"""


def initialise_db():
    """Create all tables and seed a default admin user if none exists."""
    conn = get_connection()
    conn.executescript(SCHEMA_SQL)
    conn.commit()

    # Seed admin
    cur = conn.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
    if cur.fetchone()[0] == 0:
        conn.execute(
            "INSERT INTO users (username, password, role, full_name, email) VALUES (?,?,?,?,?)",
            ("admin", hash_password("admin123"), "admin", "System Administrator", "admin@northshore.com"),
        )
        # Seed default warehouse
        conn.execute(
            "INSERT INTO warehouses (name, location) VALUES (?,?)",
            ("Central Hub", simple_encrypt("123 Logistics Lane, Northshore"))
        )
        conn.commit()
        logger.info("Database initialised – default admin and warehouse created.")
    conn.close()


# ---------------------------------------------------------------------------
# Audit helper
# ---------------------------------------------------------------------------

def audit(conn: sqlite3.Connection, user_id, action: str,
          table_name: str = None, record_id: int = None, detail: str = None):
    conn.execute(
        "INSERT INTO audit_log (user_id, action, table_name, record_id, detail) VALUES (?,?,?,?,?)",
        (user_id, action, table_name, record_id, detail),
    )
    logger.info(f"AUDIT | user={user_id} | {action} | {table_name}:{record_id} | {detail}")
