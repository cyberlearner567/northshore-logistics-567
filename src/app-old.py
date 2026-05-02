"""
app.py – Northshore Logistics Ltd
Main Tkinter GUI.  Run this file to start the application.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import datetime

# ── local modules ──────────────────────────────────────────
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import (get_connection, initialise_db, audit,
                      hash_password, simple_encrypt, simple_decrypt)
from auth import login, current_session


# ═══════════════════════════════════════════════════════════
# Colour palette & fonts
# ═══════════════════════════════════════════════════════════
BG        = "#0f1923"   # deep navy
PANEL     = "#1a2535"   # card panel
ACCENT    = "#00c9a7"   # teal accent
ACCENT2   = "#f7b731"   # amber highlight
TEXT      = "#e8edf3"   # near-white
SUBTEXT   = "#8899aa"   # muted
DANGER    = "#e74c3c"
SUCCESS   = "#2ecc71"

FONT_H1   = ("Helvetica", 20, "bold")
FONT_H2   = ("Helvetica", 14, "bold")
FONT_BODY = ("Helvetica", 11)
FONT_SM   = ("Helvetica", 9)


# ═══════════════════════════════════════════════════════════
# Helper widgets
# ═══════════════════════════════════════════════════════════

def styled_btn(parent, text, command, color=ACCENT, width=18, **kw):
    return tk.Button(parent, text=text, command=command,
                     bg=color, fg=BG, font=("Helvetica", 10, "bold"),
                     activebackground=ACCENT2, activeforeground=BG,
                     relief="flat", cursor="hand2", width=width,
                     padx=6, pady=4, **kw)


def label(parent, text, font=FONT_BODY, fg=TEXT, **kw):
    return tk.Label(parent, text=text, font=font, fg=fg, bg=PANEL, **kw)


def entry_row(parent, lbl_text, row, show=None):
    label(parent, lbl_text + ":", fg=SUBTEXT).grid(row=row, column=0,
                                                    sticky="e", padx=(0, 8), pady=4)
    var = tk.StringVar()
    e = tk.Entry(parent, textvariable=var, font=FONT_BODY,
                 bg="#253040", fg=TEXT, insertbackground=ACCENT,
                 relief="flat", bd=4, width=32, show=show or "")
    e.grid(row=row, column=1, sticky="w", pady=4)
    return var


def combo_row(parent, lbl_text, options, row):
    label(parent, lbl_text + ":", fg=SUBTEXT).grid(row=row, column=0,
                                                    sticky="e", padx=(0, 8), pady=4)
    var = tk.StringVar()
    cb = ttk.Combobox(parent, textvariable=var, values=options,
                      state="readonly", font=FONT_BODY, width=30)
    cb.grid(row=row, column=1, sticky="w", pady=4)
    return var


def make_tree(parent, columns, col_widths=None, height=14):
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Treeview",
                    background=PANEL, foreground=TEXT,
                    rowheight=26, fieldbackground=PANEL,
                    font=FONT_BODY)
    style.configure("Treeview.Heading",
                    background=BG, foreground=ACCENT,
                    font=("Helvetica", 10, "bold"))
    style.map("Treeview", background=[("selected", ACCENT)],
              foreground=[("selected", BG)])

    frame = tk.Frame(parent, bg=PANEL)
    frame.pack(fill="both", expand=True, padx=10, pady=8)

    sb = tk.Scrollbar(frame, bg=PANEL)
    sb.pack(side="right", fill="y")

    tree = ttk.Treeview(frame, columns=columns, show="headings",
                         height=height, yscrollcommand=sb.set)
    sb.config(command=tree.yview)

    for i, col in enumerate(columns):
        w = col_widths[i] if col_widths else 120
        tree.heading(col, text=col)
        tree.column(col, width=w, anchor="center")

    tree.pack(fill="both", expand=True)
    return tree


# ═══════════════════════════════════════════════════════════
# Login window
# ═══════════════════════════════════════════════════════════

class LoginWindow(tk.Toplevel):
    def __init__(self, master, on_success):
        super().__init__(master)
        self.title("Northshore Logistics – Login")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.on_success = on_success

        # Center
        self.geometry("400x340")
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 400) // 2
        y = (self.winfo_screenheight() - 340) // 2
        self.geometry(f"400x340+{x}+{y}")

        card = tk.Frame(self, bg=PANEL, pady=30, padx=40)
        card.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(card, text="🚚", font=("Helvetica", 36), bg=PANEL, fg=ACCENT).pack()
        tk.Label(card, text="NORTHSHORE LOGISTICS", font=("Helvetica", 13, "bold"),
                 bg=PANEL, fg=TEXT).pack(pady=(4, 0))
        tk.Label(card, text="Centralised Management System", font=FONT_SM,
                 bg=PANEL, fg=SUBTEXT).pack(pady=(0, 18))

        f = tk.Frame(card, bg=PANEL)
        f.pack()
        self.username_var = entry_row(f, "Username", 0)
        self.password_var = entry_row(f, "Password", 1, show="●")

        self.msg_lbl = tk.Label(card, text="", font=FONT_SM, bg=PANEL, fg=DANGER)
        self.msg_lbl.pack(pady=4)

        styled_btn(card, "Login", self._do_login, width=22).pack(pady=6)

        self.bind("<Return>", lambda e: self._do_login())
        self.protocol("WM_DELETE_WINDOW", master.destroy)

    def _do_login(self):
        ok, msg = login(self.username_var.get().strip(),
                        self.password_var.get())
        if ok:
            self.destroy()
            self.on_success()
        else:
            self.msg_lbl.config(text=msg)


# ═══════════════════════════════════════════════════════════
# Main Application
# ═══════════════════════════════════════════════════════════

class NorthshoreApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Northshore Logistics Ltd – Database System")
        self.configure(bg=BG)
        self.state("zoomed")  # maximise on startup
        self.withdraw()       # hide until login

        initialise_db()

        # Show login first
        LoginWindow(self, self._after_login)
        self.wait_window(self.children.get("!loginwindow"))

    def _after_login(self):
        self.deiconify()
        self._build_ui()

    # ----------------------------------------------------------
    # Main layout
    # ----------------------------------------------------------

    def _build_ui(self):
        # Sidebar
        self.sidebar = tk.Frame(self, bg=PANEL, width=200)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Header inside sidebar
        tk.Label(self.sidebar, text="🚚", font=("Helvetica", 28),
                 bg=PANEL, fg=ACCENT).pack(pady=(20, 0))
        tk.Label(self.sidebar, text="NORTHSHORE", font=("Helvetica", 11, "bold"),
                 bg=PANEL, fg=TEXT).pack()
        tk.Label(self.sidebar, text="LOGISTICS", font=("Helvetica", 9, "bold"),
                 bg=PANEL, fg=SUBTEXT).pack()

        tk.Frame(self.sidebar, bg=ACCENT, height=1).pack(fill="x", padx=16, pady=14)

        # User info
        tk.Label(self.sidebar, text=current_session.full_name, font=FONT_SM,
                 bg=PANEL, fg=TEXT, wraplength=170).pack()
        tk.Label(self.sidebar, text=f"[{current_session.role.upper()}]", font=FONT_SM,
                 bg=PANEL, fg=ACCENT2).pack(pady=(0, 14))

        # Nav buttons
        nav_items = [
            ("📊  Dashboard",    "dashboard",   self._show_dashboard),
            ("📦  Shipments",    "shipments",   self._show_shipments),
            ("🏭  Inventory",    "inventory",   self._show_inventory),
            ("🚐  Vehicles",     "vehicles",    self._show_vehicles),
            ("🧑‍✈️  Drivers",    "drivers",     self._show_drivers),
            ("👤  Customers",    "customers",   self._show_customers),
            ("⚠️  Incidents",    "incidents",   self._show_incidents),
            ("📈  Reports",      "reports",     self._show_reports),
            ("👥  Users",        "users",       self._show_users),
            ("🔍  Audit Log",    "audit",       self._show_audit),
        ]

        self.nav_btns = {}
        for label_text, screen, cmd in nav_items:
            if current_session.can(screen):
                btn = tk.Button(self.sidebar, text=label_text, command=cmd,
                                bg=PANEL, fg=TEXT, font=FONT_SM,
                                activebackground=ACCENT, activeforeground=BG,
                                relief="flat", anchor="w", padx=20, pady=8,
                                cursor="hand2", width=22)
                btn.pack(fill="x")
                self.nav_btns[screen] = btn

        tk.Frame(self.sidebar, bg=ACCENT, height=1).pack(fill="x", padx=16, pady=14)
        styled_btn(self.sidebar, "🔒 Logout", self._logout,
                   color=DANGER, width=20).pack(pady=4)

        # Content area
        self.content = tk.Frame(self, bg=BG)
        self.content.pack(side="right", fill="both", expand=True)

        self._show_dashboard()

    def _clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    def _page_header(self, title: str, subtitle: str = ""):
        h = tk.Frame(self.content, bg=BG, pady=16, padx=24)
        h.pack(fill="x")
        tk.Label(h, text=title, font=FONT_H1, bg=BG, fg=TEXT).pack(side="left")
        if subtitle:
            tk.Label(h, text=subtitle, font=FONT_SM, bg=BG, fg=SUBTEXT).pack(
                side="left", padx=(12, 0), anchor="s", pady=6)

    # ──────────────────────────────────────────────────────
    # DASHBOARD
    # ──────────────────────────────────────────────────────

    def _show_dashboard(self):
        self._clear_content()
        self._page_header("📊 Dashboard", "Real-time operational overview")

        conn = get_connection()

        def stat(label_text, query):
            r = conn.execute(query).fetchone()
            return r[0] if r else 0

        stats = [
            ("Total Shipments",   "SELECT COUNT(*) FROM shipments"),
            ("In Transit",        "SELECT COUNT(*) FROM shipments WHERE status='in_transit'"),
            ("Delivered Today",   f"SELECT COUNT(*) FROM shipments WHERE status='delivered' "
                                  f"AND date(delivery_date)=date('now')"),
            ("Open Incidents",    "SELECT COUNT(*) FROM incidents WHERE resolved=0"),
            ("Active Vehicles",   "SELECT COUNT(*) FROM vehicles WHERE status='in_transit'"),
            ("Inventory Items",   "SELECT COUNT(*) FROM inventory"),
        ]

        cards = tk.Frame(self.content, bg=BG, padx=24)
        cards.pack(fill="x", pady=8)

        colors = [ACCENT, ACCENT2, SUCCESS, DANGER, "#9b59b6", "#3498db"]

        for i, (lbl, q) in enumerate(stats):
            v = stat(lbl, q)
            c = tk.Frame(cards, bg=PANEL, pady=18, padx=22, relief="flat")
            c.grid(row=i // 3, column=i % 3, padx=10, pady=10, sticky="nsew")
            cards.columnconfigure(i % 3, weight=1)
            tk.Label(c, text=str(v), font=("Helvetica", 30, "bold"),
                     bg=PANEL, fg=colors[i]).pack()
            tk.Label(c, text=lbl, font=FONT_SM,
                     bg=PANEL, fg=SUBTEXT).pack()

        # Recent shipments
        tf = tk.Frame(self.content, bg=PANEL, padx=16, pady=12, relief="flat")
        tf.pack(fill="both", expand=True, padx=24, pady=12)
        tk.Label(tf, text="Recent Shipments", font=FONT_H2,
                 bg=PANEL, fg=TEXT).pack(anchor="w", pady=(0, 6))

        cols = ("Order No", "Customer", "Status", "Created")
        widths = (150, 200, 120, 150)
        tree = make_tree(tf, cols, widths, height=10)

        rows = conn.execute(
            """SELECT s.order_number, c.name, s.status, s.created_at
               FROM shipments s JOIN customers c ON s.customer_id=c.customer_id
               ORDER BY s.shipment_id DESC LIMIT 30"""
        ).fetchall()

        for r in rows:
            tree.insert("", "end", values=(r[0], r[1], r[2].upper(), r[3][:16]))

        conn.close()

        # Low stock alert
        conn2 = get_connection()
        low = conn2.execute(
            "SELECT item_name, quantity, reorder_level FROM inventory "
            "WHERE quantity <= reorder_level LIMIT 5"
        ).fetchall()
        conn2.close()

        if low:
            af = tk.Frame(self.content, bg=PANEL, padx=16, pady=10)
            af.pack(fill="x", padx=24, pady=(0, 12))
            tk.Label(af, text="⚠️  Low Stock Alerts", font=FONT_H2,
                     bg=PANEL, fg=ACCENT2).pack(anchor="w")
            for item in low:
                tk.Label(af, text=f"  • {item[0]}: {item[1]} units (reorder at {item[2]})",
                         font=FONT_SM, bg=PANEL, fg=DANGER).pack(anchor="w")

    # ──────────────────────────────────────────────────────
    # SHIPMENTS
    # ──────────────────────────────────────────────────────

    def _show_shipments(self):
        self._clear_content()
        self._page_header("📦 Shipments", "Manage all shipment records")

        # Toolbar
        tb = tk.Frame(self.content, bg=BG, padx=24)
        tb.pack(fill="x", pady=6)

        self._ship_search = tk.StringVar()
        tk.Entry(tb, textvariable=self._ship_search, font=FONT_BODY,
                 bg=PANEL, fg=TEXT, insertbackground=ACCENT,
                 relief="flat", bd=4, width=30).pack(side="left", padx=(0, 8))
        styled_btn(tb, "🔍 Search", self._search_shipments, width=12).pack(side="left", padx=4)
        styled_btn(tb, "➕ Add Shipment", self._add_shipment_dialog, width=16).pack(side="left", padx=4)
        styled_btn(tb, "✏️ Update Status", self._update_shipment_status, width=16).pack(side="left", padx=4)
        styled_btn(tb, "🔄 Refresh", self._refresh_shipments, width=12).pack(side="left", padx=4)

        # Table
        cols = ("ID", "Order No", "Customer", "Status", "Driver", "Cost (£)", "Payment", "Created")
        widths = (50, 130, 160, 100, 130, 80, 90, 120)
        self._ship_tree = make_tree(self.content, cols, widths, height=18)

        self._refresh_shipments()

    def _refresh_shipments(self, filter_text=""):
        self._ship_tree.delete(*self._ship_tree.get_children())
        conn = get_connection()
        q = """SELECT s.shipment_id, s.order_number, c.name, s.status,
                      COALESCE(u.full_name,'—') as driver,
                      s.transport_cost, s.payment_status, s.created_at
               FROM shipments s
               JOIN customers c ON s.customer_id=c.customer_id
               LEFT JOIN drivers d ON s.driver_id=d.driver_id
               LEFT JOIN users u ON d.user_id=u.user_id"""
        if filter_text:
            q += f" WHERE s.order_number LIKE '%{filter_text}%' OR c.name LIKE '%{filter_text}%'"
        q += " ORDER BY s.shipment_id DESC"
        for r in conn.execute(q).fetchall():
            self._ship_tree.insert("", "end",
                values=(r[0], r[1], r[2], r[3].upper(), r[4],
                        f"£{r[5]:.2f}", r[6], r[7][:16]))
        conn.close()

    def _search_shipments(self):
        self._refresh_shipments(self._ship_search.get().strip())

    def _add_shipment_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("Add New Shipment")
        dlg.configure(bg=BG)
        dlg.resizable(False, False)
        dlg.geometry("500x520")

        card = tk.Frame(dlg, bg=PANEL, padx=30, pady=24)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(card, text="New Shipment", font=FONT_H2, bg=PANEL, fg=ACCENT).grid(
            row=0, columnspan=2, pady=(0, 12))

        conn = get_connection()
        customers = conn.execute("SELECT customer_id, name FROM customers").fetchall()
        warehouses = conn.execute("SELECT warehouse_id, name FROM warehouses").fetchall()
        conn.close()

        cust_opts = [f"{c[0]} – {c[1]}" for c in customers]
        wh_opts   = [f"{w[0]} – {w[1]}" for w in warehouses]

        order_var  = entry_row(card, "Order Number",   1)
        cust_var   = combo_row(card, "Customer",       cust_opts, 2)
        wh_var     = combo_row(card, "Origin Warehouse", wh_opts, 3)
        dest_var   = entry_row(card, "Destination",    4)
        desc_var   = entry_row(card, "Item Description", 5)
        weight_var = entry_row(card, "Weight (kg)",    6)
        cost_var   = entry_row(card, "Transport Cost (£)", 7)

        msg = tk.Label(card, text="", font=FONT_SM, bg=PANEL, fg=DANGER)
        msg.grid(row=8, columnspan=2, pady=4)

        def save():
            # Validation
            if not order_var.get().strip():
                msg.config(text="Order number is required.")
                return
            if not cust_var.get():
                msg.config(text="Please select a customer.")
                return
            if not wh_var.get():
                msg.config(text="Please select a warehouse.")
                return
            if not dest_var.get().strip():
                msg.config(text="Destination is required.")
                return
            try:
                weight = float(weight_var.get() or 0)
                cost   = float(cost_var.get() or 0)
            except ValueError:
                msg.config(text="Weight and cost must be numbers.")
                return

            cust_id = int(cust_var.get().split("–")[0].strip())
            wh_id   = int(wh_var.get().split("–")[0].strip())

            conn2 = get_connection()
            try:
                cur = conn2.execute(
                    """INSERT INTO shipments
                       (order_number, customer_id, origin_warehouse,
                        destination_addr, item_description, weight_kg, transport_cost)
                       VALUES (?,?,?,?,?,?,?)""",
                    (order_var.get().strip(), cust_id, wh_id,
                     simple_encrypt(dest_var.get().strip()),
                     desc_var.get().strip(), weight, cost)
                )
                audit(conn2, current_session.user_id, "INSERT", "shipments",
                      cur.lastrowid, f"Order {order_var.get()}")
                conn2.commit()
                messagebox.showinfo("Success", "Shipment added successfully!", parent=dlg)
                dlg.destroy()
                self._refresh_shipments()
            except Exception as e:
                msg.config(text=str(e))
            finally:
                conn2.close()

        styled_btn(card, "💾 Save Shipment", save, width=20).grid(
            row=9, columnspan=2, pady=12)

    def _update_shipment_status(self):
        selected = self._ship_tree.selection()
        if not selected:
            messagebox.showwarning("Select Row", "Please select a shipment first.")
            return
        ship_id = self._ship_tree.item(selected[0])["values"][0]

        dlg = tk.Toplevel(self)
        dlg.title("Update Shipment")
        dlg.configure(bg=BG)
        dlg.geometry("420x340")

        card = tk.Frame(dlg, bg=PANEL, padx=30, pady=24)
        card.pack(fill="both", expand=True, padx=20, pady=20)
        tk.Label(card, text="Update Shipment", font=FONT_H2, bg=PANEL, fg=ACCENT).grid(
            row=0, columnspan=2, pady=(0, 12))

        conn = get_connection()
        drivers  = conn.execute(
            "SELECT d.driver_id, u.full_name FROM drivers d JOIN users u ON d.user_id=u.user_id"
        ).fetchall()
        vehicles = conn.execute(
            "SELECT vehicle_id, registration FROM vehicles WHERE status='available'"
        ).fetchall()
        conn.close()

        drv_opts  = ["—"] + [f"{d[0]} – {d[1]}" for d in drivers]
        veh_opts  = ["—"] + [f"{v[0]} – {v[1]}" for v in vehicles]

        status_var = combo_row(card, "New Status",
                               ["pending","in_transit","delivered","delayed","returned","cancelled"],
                               1)
        drv_var    = combo_row(card, "Assign Driver", drv_opts, 2)
        veh_var    = combo_row(card, "Assign Vehicle", veh_opts, 3)
        route_var  = entry_row(card, "Route Details", 4)
        date_var   = entry_row(card, "Delivery Date (YYYY-MM-DD)", 5)

        def save():
            conn2 = get_connection()
            updates, params = [], []
            if status_var.get():
                updates.append("status=?"); params.append(status_var.get())
            if drv_var.get() and drv_var.get() != "—":
                d_id = int(drv_var.get().split("–")[0].strip())
                updates.append("driver_id=?"); params.append(d_id)
            if veh_var.get() and veh_var.get() != "—":
                v_id = int(veh_var.get().split("–")[0].strip())
                updates.append("vehicle_id=?"); params.append(v_id)
            if route_var.get().strip():
                updates.append("route_details=?"); params.append(route_var.get().strip())
            if date_var.get().strip():
                updates.append("delivery_date=?"); params.append(date_var.get().strip())
            updates.append("updated_at=datetime('now')")
            params.append(ship_id)
            conn2.execute(f"UPDATE shipments SET {', '.join(updates)} WHERE shipment_id=?", params)
            audit(conn2, current_session.user_id, "UPDATE", "shipments", ship_id, "Status updated")
            conn2.commit()
            conn2.close()
            messagebox.showinfo("Success", "Shipment updated!", parent=dlg)
            dlg.destroy()
            self._refresh_shipments()

        styled_btn(card, "💾 Save", save, width=18).grid(row=6, columnspan=2, pady=14)

    # ──────────────────────────────────────────────────────
    # INVENTORY
    # ──────────────────────────────────────────────────────

    def _show_inventory(self):
        self._clear_content()
        self._page_header("🏭 Inventory", "Stock levels across all warehouses")

        tb = tk.Frame(self.content, bg=BG, padx=24)
        tb.pack(fill="x", pady=6)
        styled_btn(tb, "➕ Add Item", self._add_inventory_dialog, width=14).pack(side="left", padx=4)
        styled_btn(tb, "✏️ Update Qty", self._update_inventory_qty, width=14).pack(side="left", padx=4)
        styled_btn(tb, "🔄 Refresh", self._refresh_inventory, width=12).pack(side="left", padx=4)

        cols = ("ID", "Warehouse", "Item Name", "SKU", "Qty", "Reorder Lvl", "Unit", "Updated")
        widths = (50, 150, 160, 100, 60, 90, 70, 130)
        self._inv_tree = make_tree(self.content, cols, widths, height=18)
        self._refresh_inventory()

    def _refresh_inventory(self):
        self._inv_tree.delete(*self._inv_tree.get_children())
        conn = get_connection()
        rows = conn.execute(
            """SELECT i.inventory_id, w.name, i.item_name, i.sku,
                      i.quantity, i.reorder_level, i.unit, i.last_updated
               FROM inventory i JOIN warehouses w ON i.warehouse_id=w.warehouse_id
               ORDER BY i.inventory_id"""
        ).fetchall()
        conn.close()
        for r in rows:
            tag = "low" if r[4] <= r[5] else ""
            self._inv_tree.insert("", "end",
                values=(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7][:16]),
                tags=(tag,))
        self._inv_tree.tag_configure("low", foreground=DANGER)

    def _add_inventory_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("Add Inventory Item")
        dlg.configure(bg=BG)
        dlg.geometry("440x380")
        card = tk.Frame(dlg, bg=PANEL, padx=30, pady=24)
        card.pack(fill="both", expand=True, padx=20, pady=20)
        tk.Label(card, text="Add Inventory Item", font=FONT_H2,
                 bg=PANEL, fg=ACCENT).grid(row=0, columnspan=2, pady=(0, 12))

        conn = get_connection()
        whs = conn.execute("SELECT warehouse_id, name FROM warehouses").fetchall()
        conn.close()
        wh_opts = [f"{w[0]} – {w[1]}" for w in whs]

        wh_var    = combo_row(card, "Warehouse", wh_opts, 1)
        name_var  = entry_row(card, "Item Name", 2)
        sku_var   = entry_row(card, "SKU",       3)
        qty_var   = entry_row(card, "Quantity",  4)
        rl_var    = entry_row(card, "Reorder Level", 5)
        unit_var  = entry_row(card, "Unit",      6)
        msg = tk.Label(card, text="", font=FONT_SM, bg=PANEL, fg=DANGER)
        msg.grid(row=7, columnspan=2)

        def save():
            if not name_var.get().strip() or not sku_var.get().strip():
                msg.config(text="Item name and SKU are required."); return
            try:
                qty = int(qty_var.get() or 0)
                rl  = int(rl_var.get() or 10)
            except ValueError:
                msg.config(text="Quantity and reorder level must be integers."); return
            wh_id = int(wh_var.get().split("–")[0].strip())
            conn2 = get_connection()
            try:
                cur = conn2.execute(
                    "INSERT INTO inventory (warehouse_id,item_name,sku,quantity,reorder_level,unit) VALUES (?,?,?,?,?,?)",
                    (wh_id, name_var.get().strip(), sku_var.get().strip(),
                     qty, rl, unit_var.get().strip() or "units")
                )
                audit(conn2, current_session.user_id, "INSERT", "inventory", cur.lastrowid, name_var.get())
                conn2.commit()
                messagebox.showinfo("Success", "Item added!", parent=dlg)
                dlg.destroy(); self._refresh_inventory()
            except Exception as e:
                msg.config(text=str(e))
            finally:
                conn2.close()

        styled_btn(card, "💾 Save", save, width=18).grid(row=8, columnspan=2, pady=12)

    def _update_inventory_qty(self):
        sel = self._inv_tree.selection()
        if not sel:
            messagebox.showwarning("Select Row", "Please select an inventory item."); return
        inv_id = self._inv_tree.item(sel[0])["values"][0]
        new_qty = simpledialog.askinteger("Update Quantity", "Enter new quantity:", parent=self)
        if new_qty is None: return
        conn = get_connection()
        conn.execute("UPDATE inventory SET quantity=?, last_updated=datetime('now') WHERE inventory_id=?",
                     (new_qty, inv_id))
        audit(conn, current_session.user_id, "UPDATE", "inventory", inv_id, f"qty→{new_qty}")
        conn.commit(); conn.close()
        self._refresh_inventory()

    # ──────────────────────────────────────────────────────
    # VEHICLES
    # ──────────────────────────────────────────────────────

    def _show_vehicles(self):
        self._clear_content()
        self._page_header("🚐 Fleet Management", "Vehicles and maintenance")

        tb = tk.Frame(self.content, bg=BG, padx=24)
        tb.pack(fill="x", pady=6)
        styled_btn(tb, "➕ Add Vehicle", self._add_vehicle_dialog, width=14).pack(side="left", padx=4)
        styled_btn(tb, "✏️ Update Status", self._update_vehicle_status, width=16).pack(side="left", padx=4)
        styled_btn(tb, "🔄 Refresh", self._refresh_vehicles, width=12).pack(side="left", padx=4)

        cols = ("ID", "Registration", "Type", "Capacity (kg)", "Status", "Last Service", "Next Service")
        widths = (50, 120, 120, 110, 110, 130, 130)
        self._veh_tree = make_tree(self.content, cols, widths, height=18)
        self._refresh_vehicles()

    def _refresh_vehicles(self):
        self._veh_tree.delete(*self._veh_tree.get_children())
        conn = get_connection()
        for r in conn.execute("SELECT vehicle_id,registration,vehicle_type,capacity_kg,"
                               "status,last_service,next_service FROM vehicles ORDER BY vehicle_id").fetchall():
            self._veh_tree.insert("", "end", values=(
                r[0], r[1], r[2], r[3], r[4].upper(),
                r[5] or "—", r[6] or "—"))
        conn.close()

    def _add_vehicle_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("Add Vehicle")
        dlg.configure(bg=BG); dlg.geometry("440x360")
        card = tk.Frame(dlg, bg=PANEL, padx=30, pady=24)
        card.pack(fill="both", expand=True, padx=20, pady=20)
        tk.Label(card, text="Add Vehicle", font=FONT_H2, bg=PANEL, fg=ACCENT).grid(
            row=0, columnspan=2, pady=(0, 12))
        reg_var  = entry_row(card, "Registration", 1)
        type_var = combo_row(card, "Type", ["Van","Lorry","Truck","Motorcycle","Car"], 2)
        cap_var  = entry_row(card, "Capacity (kg)", 3)
        ls_var   = entry_row(card, "Last Service (YYYY-MM-DD)", 4)
        ns_var   = entry_row(card, "Next Service (YYYY-MM-DD)", 5)
        msg = tk.Label(card, text="", font=FONT_SM, bg=PANEL, fg=DANGER)
        msg.grid(row=6, columnspan=2)

        def save():
            if not reg_var.get().strip():
                msg.config(text="Registration is required."); return
            try: cap = float(cap_var.get() or 0)
            except ValueError: msg.config(text="Capacity must be a number."); return
            conn2 = get_connection()
            try:
                cur = conn2.execute(
                    "INSERT INTO vehicles (registration,vehicle_type,capacity_kg,last_service,next_service) VALUES (?,?,?,?,?)",
                    (reg_var.get().strip().upper(), type_var.get() or "Van", cap,
                     ls_var.get().strip() or None, ns_var.get().strip() or None)
                )
                audit(conn2, current_session.user_id, "INSERT", "vehicles", cur.lastrowid, reg_var.get())
                conn2.commit()
                messagebox.showinfo("Success", "Vehicle added!", parent=dlg)
                dlg.destroy(); self._refresh_vehicles()
            except Exception as e:
                msg.config(text=str(e))
            finally:
                conn2.close()

        styled_btn(card, "💾 Save", save, width=18).grid(row=7, columnspan=2, pady=12)

    def _update_vehicle_status(self):
        sel = self._veh_tree.selection()
        if not sel:
            messagebox.showwarning("Select Row", "Please select a vehicle."); return
        veh_id = self._veh_tree.item(sel[0])["values"][0]
        statuses = ["available", "in_transit", "maintenance", "retired"]
        dlg = tk.Toplevel(self)
        dlg.title("Update Vehicle Status")
        dlg.configure(bg=BG); dlg.geometry("320x200")
        card = tk.Frame(dlg, bg=PANEL, padx=30, pady=24)
        card.pack(fill="both", expand=True, padx=20, pady=20)
        st_var = combo_row(card, "New Status", statuses, 0)
        def save():
            if not st_var.get(): return
            conn = get_connection()
            conn.execute("UPDATE vehicles SET status=? WHERE vehicle_id=?", (st_var.get(), veh_id))
            audit(conn, current_session.user_id, "UPDATE", "vehicles", veh_id, f"status→{st_var.get()}")
            conn.commit(); conn.close()
            dlg.destroy(); self._refresh_vehicles()
        styled_btn(card, "💾 Save", save, width=16).grid(row=1, columnspan=2, pady=14)

    # ──────────────────────────────────────────────────────
    # DRIVERS
    # ──────────────────────────────────────────────────────

    def _show_drivers(self):
        self._clear_content()
        self._page_header("🧑‍✈️ Drivers", "Driver profiles and assignments")

        tb = tk.Frame(self.content, bg=BG, padx=24)
        tb.pack(fill="x", pady=6)
        styled_btn(tb, "➕ Add Driver", self._add_driver_dialog, width=14).pack(side="left", padx=4)
        styled_btn(tb, "🔄 Refresh",   self._refresh_drivers, width=12).pack(side="left", padx=4)

        cols = ("ID", "Full Name", "License No", "Expiry", "Status", "Warehouse")
        widths = (50, 170, 120, 100, 100, 150)
        self._drv_tree = make_tree(self.content, cols, widths, height=18)
        self._refresh_drivers()

    def _refresh_drivers(self):
        self._drv_tree.delete(*self._drv_tree.get_children())
        conn = get_connection()
        for r in conn.execute(
            """SELECT d.driver_id, u.full_name, d.license_number, d.license_expiry,
                      d.status, COALESCE(w.name,'—')
               FROM drivers d
               JOIN users u ON d.user_id=u.user_id
               LEFT JOIN warehouses w ON d.warehouse_id=w.warehouse_id
               ORDER BY d.driver_id"""
        ).fetchall():
            # Decrypt license for display (first 4 chars + asterisks)
            lic = simple_decrypt(r[2])
            masked = lic[:4] + "****" if len(lic) > 4 else lic
            self._drv_tree.insert("", "end", values=(r[0], r[1], masked, r[3], r[4].upper(), r[5]))
        conn.close()

    def _add_driver_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("Add Driver")
        dlg.configure(bg=BG); dlg.geometry("480x500")
        card = tk.Frame(dlg, bg=PANEL, padx=30, pady=24)
        card.pack(fill="both", expand=True, padx=20, pady=20)
        tk.Label(card, text="Add Driver", font=FONT_H2, bg=PANEL, fg=ACCENT).grid(
            row=0, columnspan=2, pady=(0, 12))

        conn = get_connection()
        # Non-driver users who aren't already drivers
        users = conn.execute(
            "SELECT u.user_id, u.full_name FROM users u "
            "WHERE u.user_id NOT IN (SELECT user_id FROM drivers WHERE user_id IS NOT NULL)"
        ).fetchall()
        whs = conn.execute("SELECT warehouse_id, name FROM warehouses").fetchall()
        conn.close()

        u_opts  = [f"{u[0]} – {u[1]}" for u in users]
        wh_opts = [f"{w[0]} – {w[1]}" for w in whs]

        user_var   = combo_row(card, "Link to User", u_opts, 1)
        lic_var    = entry_row(card, "License Number", 2)
        exp_var    = entry_row(card, "License Expiry (YYYY-MM-DD)", 3)
        phone_var  = entry_row(card, "Phone", 4)
        addr_var   = entry_row(card, "Address", 5)
        wh_var     = combo_row(card, "Home Warehouse", wh_opts, 6)
        msg = tk.Label(card, text="", font=FONT_SM, bg=PANEL, fg=DANGER)
        msg.grid(row=7, columnspan=2)

        def save():
            if not lic_var.get().strip() or not exp_var.get().strip():
                msg.config(text="License number and expiry are required."); return
            u_id  = int(user_var.get().split("–")[0].strip()) if user_var.get() else None
            wh_id = int(wh_var.get().split("–")[0].strip()) if wh_var.get() else None
            conn2 = get_connection()
            try:
                cur = conn2.execute(
                    "INSERT INTO drivers (user_id,license_number,license_expiry,phone,address,warehouse_id) "
                    "VALUES (?,?,?,?,?,?)",
                    (u_id, simple_encrypt(lic_var.get().strip()),
                     exp_var.get().strip(),
                     simple_encrypt(phone_var.get().strip()),
                     simple_encrypt(addr_var.get().strip()), wh_id)
                )
                audit(conn2, current_session.user_id, "INSERT", "drivers", cur.lastrowid,
                      f"License {lic_var.get()}")
                conn2.commit()
                messagebox.showinfo("Success", "Driver added!", parent=dlg)
                dlg.destroy(); self._refresh_drivers()
            except Exception as e:
                msg.config(text=str(e))
            finally:
                conn2.close()

        styled_btn(card, "💾 Save", save, width=18).grid(row=8, columnspan=2, pady=12)

    # ──────────────────────────────────────────────────────
    # CUSTOMERS
    # ──────────────────────────────────────────────────────

    def _show_customers(self):
        self._clear_content()
        self._page_header("👤 Customers", "Customer directory")

        tb = tk.Frame(self.content, bg=BG, padx=24)
        tb.pack(fill="x", pady=6)
        styled_btn(tb, "➕ Add Customer", self._add_customer_dialog, width=16).pack(side="left", padx=4)
        styled_btn(tb, "🔄 Refresh", self._refresh_customers, width=12).pack(side="left", padx=4)

        cols = ("ID", "Name", "Email", "Phone", "Address")
        widths = (50, 180, 180, 120, 200)
        self._cust_tree = make_tree(self.content, cols, widths, height=18)
        self._refresh_customers()

    def _refresh_customers(self):
        self._cust_tree.delete(*self._cust_tree.get_children())
        conn = get_connection()
        for r in conn.execute("SELECT customer_id,name,email,phone,address FROM customers ORDER BY customer_id").fetchall():
            phone = simple_decrypt(r[3]) if r[3] else "—"
            addr  = simple_decrypt(r[4]) if r[4] else "—"
            self._cust_tree.insert("", "end", values=(r[0], r[1], r[2] or "—", phone, addr))
        conn.close()

    def _add_customer_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("Add Customer")
        dlg.configure(bg=BG); dlg.geometry("440x340")
        card = tk.Frame(dlg, bg=PANEL, padx=30, pady=24)
        card.pack(fill="both", expand=True, padx=20, pady=20)
        tk.Label(card, text="Add Customer", font=FONT_H2, bg=PANEL, fg=ACCENT).grid(
            row=0, columnspan=2, pady=(0, 12))
        name_var  = entry_row(card, "Full Name", 1)
        email_var = entry_row(card, "Email",     2)
        phone_var = entry_row(card, "Phone",     3)
        addr_var  = entry_row(card, "Address",   4)
        msg = tk.Label(card, text="", font=FONT_SM, bg=PANEL, fg=DANGER)
        msg.grid(row=5, columnspan=2)

        def save():
            if not name_var.get().strip():
                msg.config(text="Name is required."); return
            if not addr_var.get().strip():
                msg.config(text="Address is required."); return
            conn2 = get_connection()
            try:
                cur = conn2.execute(
                    "INSERT INTO customers (name,email,phone,address) VALUES (?,?,?,?)",
                    (name_var.get().strip(), email_var.get().strip(),
                     simple_encrypt(phone_var.get().strip()),
                     simple_encrypt(addr_var.get().strip()))
                )
                audit(conn2, current_session.user_id, "INSERT", "customers", cur.lastrowid, name_var.get())
                conn2.commit()
                messagebox.showinfo("Success", "Customer added!", parent=dlg)
                dlg.destroy(); self._refresh_customers()
            except Exception as e:
                msg.config(text=str(e))
            finally:
                conn2.close()

        styled_btn(card, "💾 Save", save, width=18).grid(row=6, columnspan=2, pady=12)

    # ──────────────────────────────────────────────────────
    # INCIDENTS
    # ──────────────────────────────────────────────────────

    def _show_incidents(self):
        self._clear_content()
        self._page_header("⚠️ Incident Reports", "Track delivery issues and resolutions")

        tb = tk.Frame(self.content, bg=BG, padx=24)
        tb.pack(fill="x", pady=6)
        styled_btn(tb, "➕ Report Incident", self._add_incident_dialog, width=18).pack(side="left", padx=4)
        styled_btn(tb, "✅ Mark Resolved",   self._resolve_incident,    width=16).pack(side="left", padx=4)
        styled_btn(tb, "🔄 Refresh",         self._refresh_incidents,   width=12).pack(side="left", padx=4)

        cols = ("ID", "Shipment", "Type", "Description", "Reported By", "Date", "Resolved")
        widths = (50, 100, 110, 200, 140, 130, 80)
        self._inc_tree = make_tree(self.content, cols, widths, height=18)
        self._refresh_incidents()

    def _refresh_incidents(self):
        self._inc_tree.delete(*self._inc_tree.get_children())
        conn = get_connection()
        for r in conn.execute(
            """SELECT i.incident_id, s.order_number, i.incident_type,
                      i.description, u.full_name, i.reported_at, i.resolved
               FROM incidents i
               JOIN shipments s ON i.shipment_id=s.shipment_id
               LEFT JOIN users u ON i.reported_by=u.user_id
               ORDER BY i.incident_id DESC"""
        ).fetchall():
            resolved = "✅ Yes" if r[6] else "❌ No"
            self._inc_tree.insert("", "end",
                values=(r[0], r[1], r[2].upper(), (r[3] or "")[:40], r[4] or "—", r[5][:16], resolved))
        conn.close()

    def _add_incident_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("Report Incident")
        dlg.configure(bg=BG); dlg.geometry("460x360")
        card = tk.Frame(dlg, bg=PANEL, padx=30, pady=24)
        card.pack(fill="both", expand=True, padx=20, pady=20)
        tk.Label(card, text="New Incident Report", font=FONT_H2,
                 bg=PANEL, fg=ACCENT).grid(row=0, columnspan=2, pady=(0, 12))

        conn = get_connection()
        ships = conn.execute("SELECT shipment_id, order_number FROM shipments").fetchall()
        conn.close()
        s_opts = [f"{s[0]} – {s[1]}" for s in ships]

        s_var    = combo_row(card, "Shipment", s_opts, 1)
        type_var = combo_row(card, "Type",
                             ["delay","route_change","damaged","failed_delivery","lost","other"], 2)
        desc_var = entry_row(card, "Description", 3)
        msg = tk.Label(card, text="", font=FONT_SM, bg=PANEL, fg=DANGER)
        msg.grid(row=4, columnspan=2)

        def save():
            if not s_var.get(): msg.config(text="Select a shipment."); return
            s_id = int(s_var.get().split("–")[0].strip())
            conn2 = get_connection()
            try:
                cur = conn2.execute(
                    "INSERT INTO incidents (shipment_id,incident_type,description,reported_by) VALUES (?,?,?,?)",
                    (s_id, type_var.get() or "other", desc_var.get().strip(),
                     current_session.user_id)
                )
                audit(conn2, current_session.user_id, "INSERT", "incidents", cur.lastrowid,
                      f"Shipment {s_id} – {type_var.get()}")
                conn2.commit()
                messagebox.showinfo("Success", "Incident reported!", parent=dlg)
                dlg.destroy(); self._refresh_incidents()
            except Exception as e:
                msg.config(text=str(e))
            finally:
                conn2.close()

        styled_btn(card, "💾 Submit", save, width=18).grid(row=5, columnspan=2, pady=12)

    def _resolve_incident(self):
        sel = self._inc_tree.selection()
        if not sel:
            messagebox.showwarning("Select Row", "Please select an incident."); return
        inc_id = self._inc_tree.item(sel[0])["values"][0]
        conn = get_connection()
        conn.execute("UPDATE incidents SET resolved=1, resolved_at=datetime('now') WHERE incident_id=?",
                     (inc_id,))
        audit(conn, current_session.user_id, "UPDATE", "incidents", inc_id, "Marked resolved")
        conn.commit(); conn.close()
        self._refresh_incidents()

    # ──────────────────────────────────────────────────────
    # REPORTS
    # ──────────────────────────────────────────────────────

    def _show_reports(self):
        self._clear_content()
        self._page_header("📈 Operational Reports", "Summaries and insights")

        conn = get_connection()

        # Shipment status breakdown
        sf = tk.Frame(self.content, bg=PANEL, padx=20, pady=16)
        sf.pack(fill="x", padx=24, pady=10)
        tk.Label(sf, text="Shipment Status Breakdown", font=FONT_H2,
                 bg=PANEL, fg=ACCENT).pack(anchor="w")

        statuses = conn.execute(
            "SELECT status, COUNT(*) FROM shipments GROUP BY status"
        ).fetchall()
        total = sum(s[1] for s in statuses) or 1
        for s in statuses:
            row_f = tk.Frame(sf, bg=PANEL)
            row_f.pack(fill="x", pady=2)
            tk.Label(row_f, text=s[0].upper().ljust(12), font=FONT_BODY,
                     bg=PANEL, fg=TEXT, width=14, anchor="w").pack(side="left")
            pct = s[1] / total
            bar_bg = tk.Frame(row_f, bg="#253040", height=18, width=300)
            bar_bg.pack(side="left", padx=8)
            bar_bg.pack_propagate(False)
            bar_fg = tk.Frame(bar_bg, bg=ACCENT, height=18, width=int(300 * pct))
            bar_fg.pack(side="left")
            tk.Label(row_f, text=f"{s[1]} ({pct*100:.0f}%)", font=FONT_SM,
                     bg=PANEL, fg=SUBTEXT).pack(side="left")

        # Vehicle utilisation
        vf = tk.Frame(self.content, bg=PANEL, padx=20, pady=16)
        vf.pack(fill="x", padx=24, pady=6)
        tk.Label(vf, text="Vehicle Utilisation", font=FONT_H2,
                 bg=PANEL, fg=ACCENT).pack(anchor="w")
        for r in conn.execute(
            "SELECT status, COUNT(*) FROM vehicles GROUP BY status"
        ).fetchall():
            tk.Label(vf, text=f"  {r[0].upper()}: {r[1]} vehicle(s)",
                     font=FONT_BODY, bg=PANEL, fg=TEXT).pack(anchor="w")

        # Warehouse activity
        wf = tk.Frame(self.content, bg=PANEL, padx=20, pady=16)
        wf.pack(fill="x", padx=24, pady=6)
        tk.Label(wf, text="Warehouse Shipment Activity", font=FONT_H2,
                 bg=PANEL, fg=ACCENT).pack(anchor="w")
        for r in conn.execute(
            """SELECT w.name, COUNT(s.shipment_id) as total
               FROM warehouses w
               LEFT JOIN shipments s ON s.origin_warehouse=w.warehouse_id
               GROUP BY w.warehouse_id"""
        ).fetchall():
            tk.Label(wf, text=f"  {r[0]}: {r[1]} shipment(s)",
                     font=FONT_BODY, bg=PANEL, fg=TEXT).pack(anchor="w")

        # Financial summary
        ff = tk.Frame(self.content, bg=PANEL, padx=20, pady=16)
        ff.pack(fill="x", padx=24, pady=6)
        tk.Label(ff, text="Financial Summary", font=FONT_H2,
                 bg=PANEL, fg=ACCENT).pack(anchor="w")
        fin = conn.execute(
            "SELECT SUM(transport_cost), SUM(surcharges), "
            "SUM(CASE WHEN payment_status='paid' THEN transport_cost ELSE 0 END) FROM shipments"
        ).fetchone()
        tk.Label(ff, text=f"  Total Revenue:  £{fin[0] or 0:.2f}",
                 font=FONT_BODY, bg=PANEL, fg=SUCCESS).pack(anchor="w")
        tk.Label(ff, text=f"  Total Surcharges: £{fin[1] or 0:.2f}",
                 font=FONT_BODY, bg=PANEL, fg=ACCENT2).pack(anchor="w")
        tk.Label(ff, text=f"  Paid Amount:    £{fin[2] or 0:.2f}",
                 font=FONT_BODY, bg=PANEL, fg=TEXT).pack(anchor="w")

        conn.close()

    # ──────────────────────────────────────────────────────
    # USERS (admin only)
    # ──────────────────────────────────────────────────────

    def _show_users(self):
        self._clear_content()
        self._page_header("👥 User Management", "Accounts and role-based access")

        tb = tk.Frame(self.content, bg=BG, padx=24)
        tb.pack(fill="x", pady=6)
        styled_btn(tb, "➕ Add User", self._add_user_dialog, width=14).pack(side="left", padx=4)
        styled_btn(tb, "🚫 Disable/Enable", self._toggle_user, width=16).pack(side="left", padx=4)
        styled_btn(tb, "🔄 Refresh", self._refresh_users, width=12).pack(side="left", padx=4)

        cols = ("ID", "Username", "Full Name", "Role", "Email", "Active", "Created")
        widths = (50, 120, 170, 100, 180, 60, 130)
        self._user_tree = make_tree(self.content, cols, widths, height=18)
        self._refresh_users()

    def _refresh_users(self):
        self._user_tree.delete(*self._user_tree.get_children())
        conn = get_connection()
        for r in conn.execute(
            "SELECT user_id,username,full_name,role,email,is_active,created_at FROM users ORDER BY user_id"
        ).fetchall():
            self._user_tree.insert("", "end",
                values=(r[0], r[1], r[2], r[3].upper(), r[4] or "—",
                        "✅" if r[5] else "❌", r[6][:16]))
        conn.close()

    def _add_user_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("Add User")
        dlg.configure(bg=BG); dlg.geometry("440x380")
        card = tk.Frame(dlg, bg=PANEL, padx=30, pady=24)
        card.pack(fill="both", expand=True, padx=20, pady=20)
        tk.Label(card, text="Add User", font=FONT_H2, bg=PANEL, fg=ACCENT).grid(
            row=0, columnspan=2, pady=(0, 12))

        user_var  = entry_row(card, "Username",  1)
        pwd_var   = entry_row(card, "Password",  2, show="●")
        name_var  = entry_row(card, "Full Name", 3)
        email_var = entry_row(card, "Email",     4)
        role_var  = combo_row(card, "Role",
                              ["admin","manager","warehouse","driver"], 5)
        msg = tk.Label(card, text="", font=FONT_SM, bg=PANEL, fg=DANGER)
        msg.grid(row=6, columnspan=2)

        def save():
            if not user_var.get().strip() or not pwd_var.get():
                msg.config(text="Username and password are required."); return
            if len(pwd_var.get()) < 6:
                msg.config(text="Password must be at least 6 characters."); return
            conn2 = get_connection()
            try:
                cur = conn2.execute(
                    "INSERT INTO users (username,password,role,full_name,email) VALUES (?,?,?,?,?)",
                    (user_var.get().strip(), hash_password(pwd_var.get()),
                     role_var.get() or "warehouse",
                     name_var.get().strip(), email_var.get().strip())
                )
                audit(conn2, current_session.user_id, "INSERT", "users", cur.lastrowid,
                      f"Created user {user_var.get()}")
                conn2.commit()
                messagebox.showinfo("Success", "User created!", parent=dlg)
                dlg.destroy(); self._refresh_users()
            except Exception as e:
                msg.config(text=str(e))
            finally:
                conn2.close()

        styled_btn(card, "💾 Save", save, width=18).grid(row=7, columnspan=2, pady=12)

    def _toggle_user(self):
        sel = self._user_tree.selection()
        if not sel:
            messagebox.showwarning("Select Row", "Please select a user."); return
        user_id = self._user_tree.item(sel[0])["values"][0]
        if user_id == current_session.user_id:
            messagebox.showwarning("Error", "You cannot disable your own account."); return
        conn = get_connection()
        cur_active = conn.execute(
            "SELECT is_active FROM users WHERE user_id=?", (user_id,)
        ).fetchone()[0]
        new_state = 0 if cur_active else 1
        conn.execute("UPDATE users SET is_active=? WHERE user_id=?", (new_state, user_id))
        audit(conn, current_session.user_id, "UPDATE", "users", user_id,
              f"is_active→{new_state}")
        conn.commit(); conn.close()
        self._refresh_users()

    # ──────────────────────────────────────────────────────
    # AUDIT LOG
    # ──────────────────────────────────────────────────────

    def _show_audit(self):
        self._clear_content()
        self._page_header("🔍 Audit Log", "All system activity")

        cols = ("Log ID", "User", "Action", "Table", "Record ID", "Detail", "Timestamp")
        widths = (70, 120, 100, 100, 80, 200, 140)
        tree = make_tree(self.content, cols, widths, height=22)

        conn = get_connection()
        for r in conn.execute(
            """SELECT al.log_id, COALESCE(u.username,'system'),
                      al.action, al.table_name, al.record_id, al.detail, al.logged_at
               FROM audit_log al
               LEFT JOIN users u ON al.user_id=u.user_id
               ORDER BY al.log_id DESC LIMIT 500"""
        ).fetchall():
            tree.insert("", "end",
                values=(r[0], r[1], r[2], r[3] or "—", r[4] or "—",
                        (r[5] or "")[:50], r[6][:19]))
        conn.close()

    # ──────────────────────────────────────────────────────
    # LOGOUT
    # ──────────────────────────────────────────────────────

    def _logout(self):
        conn = get_connection()
        audit(conn, current_session.user_id, "LOGOUT",
              detail=f"User '{current_session.username}' logged out.")
        conn.commit(); conn.close()
        current_session.logout()
        self.destroy()


# ═══════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = NorthshoreApp()
    app.mainloop()
