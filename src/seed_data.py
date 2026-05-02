"""
seed_data.py – Northshore Logistics Ltd
Populates the database with realistic sample data for testing.
Run once after initialise_db().
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import (get_connection, initialise_db, hash_password,
                      simple_encrypt, audit)
import datetime


def seed():
    initialise_db()
    conn = get_connection()

    # ── Extra users ────────────────────────────────────────
    users = [
        ("manager1",  "manager123",  "manager",   "Sarah Johnson",   "sarah@northshore.com"),
        ("warehouse1","wh123456",    "warehouse", "James Miller",    "james@northshore.com"),
        ("warehouse2","wh123456",    "warehouse", "Emma Wilson",     "emma@northshore.com"),
        ("driver1",   "driver123",   "driver",    "Mohammed Al-Amin","mo@northshore.com"),
        ("driver2",   "driver123",   "driver",    "Laura Chen",      "laura@northshore.com"),
        ("driver3",   "driver123",   "driver",    "David Okonkwo",   "david@northshore.com"),
    ]
    user_ids = {}
    for u in users:
        try:
            cur = conn.execute(
                "INSERT INTO users (username,password,role,full_name,email) VALUES (?,?,?,?,?)",
                (u[0], hash_password(u[1]), u[2], u[3], u[4])
            )
            user_ids[u[0]] = cur.lastrowid
        except Exception:
            row = conn.execute("SELECT user_id FROM users WHERE username=?", (u[0],)).fetchone()
            if row: user_ids[u[0]] = row[0]

    # ── Extra warehouses ───────────────────────────────────
    wh_ids = []
    for name, loc in [
        ("Northern Depot",  "45 Industrial Road, Manchester"),
        ("Southern Hub",    "22 Commerce Lane, Southampton"),
        ("Eastern Gateway", "87 Port Way, Felixstowe"),
    ]:
        try:
            cur = conn.execute(
                "INSERT INTO warehouses (name,location) VALUES (?,?)",
                (name, simple_encrypt(loc))
            )
            wh_ids.append(cur.lastrowid)
        except Exception:
            pass

    # Get all warehouse ids
    all_wh = [r[0] for r in conn.execute("SELECT warehouse_id FROM warehouses").fetchall()]

    # ── Vehicles ───────────────────────────────────────────
    veh_data = [
        ("LN72 ABC", "Van",   1200, "available",  "2024-06-01", "2025-06-01"),
        ("MN21 XYZ", "Lorry", 8000, "available",  "2024-08-15", "2025-08-15"),
        ("SO19 DEF", "Truck", 20000,"maintenance","2024-01-10", "2025-01-10"),
        ("EG73 GHI", "Van",   1200, "in_transit", "2024-09-20", "2025-09-20"),
        ("LN55 JKL", "Van",   1500, "available",  "2024-11-01", "2025-11-01"),
    ]
    veh_ids = []
    for v in veh_data:
        try:
            cur = conn.execute(
                "INSERT INTO vehicles (registration,vehicle_type,capacity_kg,status,last_service,next_service) "
                "VALUES (?,?,?,?,?,?)", v
            )
            veh_ids.append(cur.lastrowid)
        except Exception:
            pass

    # ── Drivers ────────────────────────────────────────────
    drv_user_keys = ["driver1", "driver2", "driver3"]
    drv_data = [
        ("DL123456789", "2027-05-01", "07700900001", "10 Driver Street, Manchester"),
        ("DL987654321", "2026-08-30", "07700900002", "5 Route Avenue, Southampton"),
        ("DL555000111", "2028-01-15", "07700900003", "8 Delivery Close, Felixstowe"),
    ]
    drv_ids = []
    for i, dd in enumerate(drv_data):
        uid = user_ids.get(drv_user_keys[i])
        wh  = all_wh[i % len(all_wh)] if all_wh else None
        try:
            cur = conn.execute(
                "INSERT INTO drivers (user_id,license_number,license_expiry,phone,address,warehouse_id) VALUES (?,?,?,?,?,?)",
                (uid, simple_encrypt(dd[0]), dd[1],
                 simple_encrypt(dd[2]), simple_encrypt(dd[3]), wh)
            )
            drv_ids.append(cur.lastrowid)
        except Exception:
            pass

    all_drv = [r[0] for r in conn.execute("SELECT driver_id FROM drivers").fetchall()]

    # ── Customers ──────────────────────────────────────────
    cust_data = [
        ("Acme Electronics",  "orders@acme.co.uk",   "01234567890", "1 Tech Park, London"),
        ("Green Garden Co",   "buy@greengarden.com",  "01987654321", "22 Garden Way, Bristol"),
        ("FastPack Ltd",      "info@fastpack.com",    "07800111222", "7 Box Lane, Leeds"),
        ("Northern Foods PLC","supply@nfoods.co.uk",  "01612223344", "90 Food Court, Liverpool"),
        ("Riverside Books",   "orders@rbooks.co.uk",  "01316667788", "3 Pages Road, Edinburgh"),
    ]
    cust_ids = []
    for cd in cust_data:
        try:
            cur = conn.execute(
                "INSERT INTO customers (name,email,phone,address) VALUES (?,?,?,?)",
                (cd[0], cd[1], simple_encrypt(cd[2]), simple_encrypt(cd[3]))
            )
            cust_ids.append(cur.lastrowid)
        except Exception:
            row = conn.execute("SELECT customer_id FROM customers WHERE name=?", (cd[0],)).fetchone()
            if row: cust_ids.append(row[0])

    all_cust = [r[0] for r in conn.execute("SELECT customer_id FROM customers").fetchall()]
    all_wh_now = [r[0] for r in conn.execute("SELECT warehouse_id FROM warehouses").fetchall()]
    all_veh = [r[0] for r in conn.execute("SELECT vehicle_id FROM vehicles").fetchall()]

    # ── Shipments ──────────────────────────────────────────
    shipment_data = [
        ("ORD-2026-001", 0, 0, "12 Regent St London W1",  "Electronics parcel",    4.5,  "delivered",  0, 0, 85.00, "paid"),
        ("ORD-2026-002", 1, 1, "6 High St Bristol BS1",   "Garden supplies crate", 22.0, "in_transit", 1, 1, 220.00,"unpaid"),
        ("ORD-2026-003", 2, 2, "44 Park Row Leeds LS1",   "Book boxes (×10)",      18.0, "pending",    2, 2, 150.00,"unpaid"),
        ("ORD-2026-004", 3, 0, "11 Castle St Edinburgh",  "Frozen food pallet",    80.0, "delayed",    0, 3, 430.00,"paid"),
        ("ORD-2026-005", 4, 1, "7 Ocean Way Portsmouth",  "Mixed retail goods",    35.0, "delivered",  1, 4, 310.00,"paid"),
        ("ORD-2026-006", 0, 2, "2 Mill Lane York",        "Computer components",   6.0,  "returned",   2, 0, 95.00, "refunded"),
        ("ORD-2026-007", 1, 0, "55 Beach Rd Brighton",    "Gardening tools",       14.0, "in_transit", 0, 1, 175.00,"unpaid"),
        ("ORD-2026-008", 2, 1, "9 Quay St Cardiff",       "Boxed books",           25.0, "pending",    1, 2, 200.00,"unpaid"),
    ]
    ship_ids = []
    for sd in shipment_data:
        ci  = all_cust[sd[1] % len(all_cust)]
        wi  = all_wh_now[sd[2] % len(all_wh_now)]
        di  = all_drv[sd[7] % len(all_drv)] if all_drv else None
        vi  = all_veh[sd[8] % len(all_veh)] if all_veh else None
        try:
            cur = conn.execute(
                """INSERT INTO shipments
                   (order_number,customer_id,origin_warehouse,destination_addr,
                    item_description,weight_kg,status,driver_id,vehicle_id,
                    transport_cost,payment_status)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (sd[0], ci, wi, simple_encrypt(sd[3]),
                 sd[4], sd[5], sd[6], di, vi, sd[9], sd[10])
            )
            ship_ids.append(cur.lastrowid)
        except Exception:
            pass

    all_ships = [r[0] for r in conn.execute("SELECT shipment_id FROM shipments").fetchall()]

    # ── Incidents ──────────────────────────────────────────
    incidents = [
        (all_ships[3 % len(all_ships)], "delay",         "Road closure on A1 caused 3-hour delay."),
        (all_ships[5 % len(all_ships)], "damaged",       "Corner of box crushed during loading."),
        (all_ships[6 % len(all_ships)], "route_change",  "Re-routed due to motorway accident."),
    ]
    for inc in incidents:
        try:
            conn.execute(
                "INSERT INTO incidents (shipment_id,incident_type,description,reported_by) VALUES (?,?,?,1)",
                inc
            )
        except Exception:
            pass

    # ── Inventory ──────────────────────────────────────────
    inv_data = [
        ("Cardboard Boxes (L)",   "BOX-L-001",  200, 50),
        ("Cardboard Boxes (M)",   "BOX-M-001",  350, 80),
        ("Bubble Wrap Roll",      "WRAP-001",    12,  5),
        ("Pallets (Wooden)",      "PALET-001",   34, 10),
        ("Packing Tape",          "TAPE-001",    85, 20),
        ("Stretch Film Roll",     "FILM-001",     8,  5),
        ("Scanner Handheld",      "SCAN-001",     5,  2),
        ("Safety Gloves (pairs)", "GLOVE-001",   90, 30),
    ]
    for i, item in enumerate(inv_data):
        wh_id = all_wh_now[i % len(all_wh_now)]
        try:
            conn.execute(
                "INSERT INTO inventory (warehouse_id,item_name,sku,quantity,reorder_level) VALUES (?,?,?,?,?)",
                (wh_id, item[0], item[1], item[2], item[3])
            )
        except Exception:
            pass

    conn.commit()
    conn.close()
    print("✅  Sample data seeded successfully.")


if __name__ == "__main__":
    seed()
