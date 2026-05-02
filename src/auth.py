"""
auth.py – Northshore Logistics Ltd
Handles login, logout, and role-based permission checks.
"""

from database import get_connection, verify_password, audit

# Permissions per role  {role: set of allowed screens/actions}
PERMISSIONS = {
    "admin":     {"dashboard","shipments","inventory","vehicles","drivers",
                  "customers","reports","users","audit","incidents","warehouses"},
    "manager":   {"dashboard","shipments","inventory","vehicles","drivers",
                  "customers","reports","incidents","warehouses"},
    "warehouse": {"dashboard","shipments","inventory","incidents"},
    "driver":    {"dashboard","shipments","incidents"},
}


class Session:
    """Holds the currently logged-in user's state."""
    def __init__(self):
        self.user_id = None
        self.username = None
        self.role = None
        self.full_name = None

    @property
    def is_logged_in(self) -> bool:
        return self.user_id is not None

    def can(self, screen: str) -> bool:
        """Return True if the current role may access the given screen."""
        if not self.role:
            return False
        return screen in PERMISSIONS.get(self.role, set())

    def logout(self):
        self.user_id = self.username = self.role = self.full_name = None


# Global session object
current_session = Session()


def login(username: str, password: str) -> tuple[bool, str]:
    """
    Attempt to authenticate.
    Returns (success, message).
    """
    conn = get_connection()
    row = conn.execute(
        "SELECT user_id, password, role, full_name, is_active FROM users WHERE username=?",
        (username,)
    ).fetchone()
    conn.close()

    if not row:
        return False, "User not found."
    if not row["is_active"]:
        return False, "Account is disabled."
    if not verify_password(password, row["password"]):
        return False, "Incorrect password."

    current_session.user_id = row["user_id"]
    current_session.username = username
    current_session.role = row["role"]
    current_session.full_name = row["full_name"]

    conn = get_connection()
    audit(conn, row["user_id"], "LOGIN", detail=f"User '{username}' logged in.")
    conn.commit()
    conn.close()
    return True, f"Welcome, {row['full_name']}!"
