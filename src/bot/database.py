"""
Database module for PolyTerm Telegram Bot.
Handles all database operations with SQLite.
"""
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from .data.config import sqlite_database_filepath


def get_connection() -> sqlite3.Connection:
    """Get a database connection with row factory."""
    conn = sqlite3.connect(sqlite_database_filepath)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db_cursor():
    """Context manager for database operations."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def init_database() -> None:
    """Initialize database with required tables."""
    with get_db_cursor() as cursor:
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                subscribed_until TEXT,
                subscription_active INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_active TEXT,
                is_admin INTEGER DEFAULT 0
            )
        """)

        # Payments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                tx_hash TEXT UNIQUE,
                plan_months INTEGER,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                confirmed_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Admins table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY,
                added_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Command log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS command_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                command TEXT,
                executed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)


def create_user(user_id: int, username: str = None, full_name: str = None) -> None:
    """Create a new user or update existing one."""
    with get_db_cursor() as cursor:
        cursor.execute("""
            INSERT INTO users (user_id, username, full_name, last_active)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                full_name = excluded.full_name,
                last_active = excluded.last_active
        """, (user_id, username, full_name, datetime.now().isoformat()))


def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user by ID."""
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def update_user_subscription(user_id: int, months: int) -> None:
    """Update user's subscription."""
    with get_db_cursor() as cursor:
        # Calculate new subscription end date
        user = get_user(user_id)
        if user and user['subscribed_until']:
            current_end = datetime.fromisoformat(user['subscribed_until'])
            if current_end > datetime.now():
                new_end = current_end + timedelta(days=30 * months)
            else:
                new_end = datetime.now() + timedelta(days=30 * months)
        else:
            new_end = datetime.now() + timedelta(days=30 * months)

        cursor.execute("""
            UPDATE users 
            SET subscribed_until = ?, subscription_active = 1
            WHERE user_id = ?
        """, (new_end.isoformat(), user_id))


def check_subscription_active(user_id: int) -> bool:
    """Check if user has active subscription."""
    user = get_user(user_id)
    if not user or not user['subscribed_until']:
        return False
    
    if not user['subscription_active']:
        return False
    
    subscribed_until = datetime.fromisoformat(user['subscribed_until'])
    return subscribed_until > datetime.now()


def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    with get_db_cursor() as cursor:
        cursor.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
        return cursor.fetchone() is not None


def add_admin(user_id: int) -> None:
    """Add user as admin."""
    with get_db_cursor() as cursor:
        cursor.execute("""
            INSERT OR IGNORE INTO admins (user_id) VALUES (?)
        """, (user_id,))


def create_payment(user_id: int, amount: float, tx_hash: str, plan_months: int) -> int:
    """Create a new payment record."""
    with get_db_cursor() as cursor:
        cursor.execute("""
            INSERT INTO payments (user_id, amount, tx_hash, plan_months, status)
            VALUES (?, ?, ?, ?, 'pending')
        """, (user_id, amount, tx_hash, plan_months))
        return cursor.lastrowid


def get_payment_by_txhash(tx_hash: str) -> Optional[Dict[str, Any]]:
    """Get payment by transaction hash."""
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM payments WHERE tx_hash = ?", (tx_hash,))
        row = cursor.fetchone()
        return dict(row) if row else None


def update_payment_status(payment_id: int, status: str) -> None:
    """Update payment status."""
    with get_db_cursor() as cursor:
        if status == 'confirmed':
            cursor.execute("""
                UPDATE payments 
                SET status = ?, confirmed_at = ?
                WHERE id = ?
            """, (status, datetime.now().isoformat(), payment_id))
        else:
            cursor.execute("""
                UPDATE payments SET status = ? WHERE id = ?
            """, (status, payment_id))


def get_pending_payments(user_id: int) -> List[Dict[str, Any]]:
    """Get pending payments for a user."""
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT * FROM payments WHERE user_id = ? AND status = 'pending'",
            (user_id,)
        )
        return [dict(row) for row in cursor.fetchall()]


def log_command(user_id: int, command: str) -> None:
    """Log a command execution."""
    with get_db_cursor() as cursor:
        cursor.execute("""
            INSERT INTO command_log (user_id, command, executed_at)
            VALUES (?, ?, ?)
        """, (user_id, command, datetime.now().isoformat()))


def get_all_users() -> List[Dict[str, Any]]:
    """Get all users."""
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM users")
        return [dict(row) for row in cursor.fetchall()]


def get_active_subscribers_count() -> int:
    """Get count of active subscribers."""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) FROM users 
            WHERE subscription_active = 1 
            AND subscribed_until > ?
        """, (datetime.now().isoformat(),))
        return cursor.fetchone()[0]


def get_total_revenue() -> float:
    """Get total revenue from confirmed payments."""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = 'confirmed'
        """)
        return cursor.fetchone()[0]


def get_bot_statistics() -> Dict[str, Any]:
    """Get bot statistics."""
    with get_db_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as total FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM users 
            WHERE subscription_active = 1 
            AND subscribed_until > ?
        """, (datetime.now().isoformat(),))
        active_subs = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = 'confirmed'
        """)
        total_revenue = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM payments WHERE status = 'pending'")
        pending_payments = cursor.fetchone()[0]
        
        return {
            'total_users': total_users,
            'active_subscribers': active_subs,
            'total_revenue': total_revenue,
            'pending_payments': pending_payments
        }
