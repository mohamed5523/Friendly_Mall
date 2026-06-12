"""Mall Database - SQLite local database manager."""
from __future__ import annotations
import sqlite3
import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent / "mall.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Create tables if they don't exist."""
    with get_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_ar TEXT NOT NULL UNIQUE,
            name_en TEXT NOT NULL,
            icon TEXT DEFAULT '🏠'
        );

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_ar TEXT NOT NULL,
            category_id INTEGER NOT NULL,
            sub_category TEXT,
            price REAL NOT NULL,
            stock_count INTEGER NOT NULL DEFAULT 0,
            brand TEXT,
            description_ar TEXT,
            color TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(category_id) REFERENCES categories(id)
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            customer_phone TEXT,
            quantity INTEGER NOT NULL DEFAULT 1,
            unit_price REAL NOT NULL,
            total_price REAL NOT NULL,
            status TEXT DEFAULT 'مؤكد',
            order_type TEXT DEFAULT 'شراء',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(product_id) REFERENCES products(id)
        );

        CREATE TABLE IF NOT EXISTS sales_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            category_id INTEGER,
            quantity_sold INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            revenue REAL NOT NULL,
            sale_date TEXT NOT NULL,
            FOREIGN KEY(product_id) REFERENCES products(id)
        );

        CREATE TABLE IF NOT EXISTS merchant_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            merchant_name TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            total_value REAL NOT NULL,
            order_date TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(product_id) REFERENCES products(id)
        );
        """)
    logger.info("Database initialized at %s", DB_PATH)


# ── Query helpers ──────────────────────────────────────────────────────────

def normalize_arabic_query(term: str) -> str:
    """Remove common Arabic plurals and feminine endings for better search matching."""
    if not term:
        return ""
    
    irregular_plurals = {
        "كراسي": "كرسي", "مراتب": "مرتب", "أسرّة": "سرير", "اسرة": "سرير",
        "أطباق": "طبق", "أكواب": "كوب", "مقالي": "مقل", "حلل": "حل",
        "أفران": "فرن", "خزائن": "خزان", "بوافيه": "بوفيه", "ستائر": "ستار",
        "مراوح": "مروح", "مكانس": "مكنس", "مناشف": "منشف", "مرايا": "مرآ", 
        "أوعية": "وعاء", "شموع": "شمع", "سلال": "سل", "أدوات": "أدا",
        "إطارات": "إطار", "لوحات": "لوح", "أجهزة": "جهاز",
        "تلاجات": "ثلاج", "ثلاجات": "ثلاج", "تلاجة": "ثلاج", "ثلاجة": "ثلاج",
        "تلفزيونات": "تلفزيون", "تليفزيونات": "تلفزيون", "شاشات": "شاش",
        "تكييفات": "تكييف", "مكيفات": "مكيف", "بوتاجازات": "بوتاجاز",
        "بتوجاز": "بوتاجاز", "بوتجاز": "بوتاجاز",
        "موبايلات": "موبايل", "غسالات": "غسال", "غسالة": "غسال", "غساله": "غسال",
        "لابات": "لابتوب", "لاب": "لابتوب",
        "زرقا": "أزرق", "زرقة": "أزرق", "حمره": "أحمر", "حمرا": "أحمر",
        "خضرا": "أخضر", "خضره": "أخضر", "سوده": "أسود", "سودا": "أسود",
        "بيضه": "أبيض", "بيضا": "أبيض", "صفره": "أصفر", "صفرا": "أصفر",
        "غرفة": "غرف", "غرفه": "غرف"
    }
    
    words = term.split()
    normalized = []
    suffixes = ["ات", "ون", "ين", "ة", "ه", "اء"]
    for w in words:
        if w.startswith("ال") and len(w) > 3:
            w = w[2:]
            
        if w in irregular_plurals:
            w = irregular_plurals[w]
        elif len(w) > 4:
            for suf in suffixes:
                if w.endswith(suf):
                    w = w[:-len(suf)]
                    break
        normalized.append(w)
    return " ".join(normalized)

def get_category_summary(query: str) -> Optional[Dict]:
    """
    Checks if the query matches a category name. If so, returns a summary of sub_categories and their min prices.
    Returns {"category_name": str, "sub_categories": [{"name": str, "min_price": float}]} or None.
    """
    norm_query = normalize_arabic_query(query)
    if not norm_query:
        return None
        
    cats = get_all_categories()
    matched_cat = None
    for c in cats:
        cat_norm = normalize_arabic_query(c["name_ar"])
        if cat_norm == norm_query or norm_query in cat_norm:
            matched_cat = c
            break
            
    if not matched_cat:
        return None
        
    with get_connection() as conn:
        rows = conn.execute('''
            SELECT sub_category, MIN(price) as min_price 
            FROM products 
            WHERE category_id = ? 
            GROUP BY sub_category
            ORDER BY min_price ASC
        ''', (matched_cat["id"],)).fetchall()
        
    if not rows:
        return None
        
    return {
        "category_name": matched_cat["name_ar"],
        "sub_categories": [{"name": r["sub_category"], "min_price": r["min_price"]} for r in rows]
    }

def search_products(query: str, category: Optional[str] = None, limit: int = 10) -> List[Dict]:
    """Full-text search on product names."""
    query = normalize_arabic_query(query)
    words = [w for w in query.split() if w]
    if not words:
        return []
    
    with get_connection() as conn:
        # Build AND conditions for each word
        word_conditions = " AND ".join(
            "(p.name_ar LIKE ? OR p.description_ar LIKE ? OR p.brand LIKE ?)" 
            for _ in words
        )
        # Flatten parameters: for each word we need 3 parameters
        params = []
        for w in words:
            params.extend([f"%{w}%", f"%{w}%", f"%{w}%"])
            
        if category:
            sql = f"""
                SELECT p.*, c.name_ar as category_name
                FROM products p JOIN categories c ON p.category_id = c.id
                WHERE {word_conditions}
                  AND c.name_ar LIKE ?
                LIMIT ?
            """
            params.extend([f"%{category}%", limit])
        else:
            sql = f"""
                SELECT p.*, c.name_ar as category_name
                FROM products p JOIN categories c ON p.category_id = c.id
                WHERE {word_conditions}
                LIMIT ?
            """
            params.append(limit)
            
        rows = conn.execute(sql, tuple(params)).fetchall()
        return [dict(r) for r in rows]


def get_product_by_id(product_id: int) -> Optional[Dict]:
    with get_connection() as conn:
        row = conn.execute("""
            SELECT p.*, c.name_ar as category_name
            FROM products p JOIN categories c ON p.category_id = c.id
            WHERE p.id = ?
        """, (product_id,)).fetchone()
        return dict(row) if row else None


def get_products_by_category(category_name: str, limit: int = 20) -> List[Dict]:
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT p.*, c.name_ar as category_name
            FROM products p JOIN categories c ON p.category_id = c.id
            WHERE c.name_ar LIKE ?
            ORDER BY p.price
            LIMIT ?
        """, (f"%{category_name}%", limit)).fetchall()
        return [dict(r) for r in rows]


def get_all_categories() -> List[Dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM categories ORDER BY name_ar").fetchall()
        return [dict(r) for r in rows]


def create_order(product_id: int, customer_name: str, quantity: int,
                 order_type: str = "شراء", customer_phone: str = "") -> Dict:
    product = get_product_by_id(product_id)
    if not product:
        raise ValueError("المنتج مش موجود")
    if product["stock_count"] < quantity:
        raise ValueError(f"الكمية المتاحة {product['stock_count']} فقط")

    total = product["price"] * quantity
    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO orders (product_id, product_name, customer_name, customer_phone,
                                quantity, unit_price, total_price, status, order_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'مؤكد', ?)
        """, (product_id, product["name_ar"], customer_name, customer_phone,
              quantity, product["price"], total, order_type))
        order_id = cursor.lastrowid
        # Reduce stock
        conn.execute("UPDATE products SET stock_count = stock_count - ? WHERE id = ?",
                     (quantity, product_id))
        # Record sale
        conn.execute("""
            INSERT INTO sales_history (product_id, product_name, category_id,
                                       quantity_sold, unit_price, revenue, sale_date)
            VALUES (?, ?, ?, ?, ?, ?, date('now'))
        """, (product_id, product["name_ar"], product["category_id"],
              quantity, product["price"], total))
    return {"order_id": order_id, "total_price": total, "status": "مؤكد"}


def get_order_status(order_id: int) -> Optional[Dict]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        return dict(row) if row else None


# ── Manager analytics ──────────────────────────────────────────────────────

def get_sales_report(days: int = 30) -> Dict:
    with get_connection() as conn:
        since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        total = conn.execute(
            "SELECT COALESCE(SUM(revenue),0) as rev, COALESCE(SUM(quantity_sold),0) as qty FROM sales_history WHERE sale_date >= ?",
            (since,)).fetchone()
        by_cat = conn.execute("""
            SELECT c.name_ar, SUM(s.revenue) as revenue, SUM(s.quantity_sold) as qty
            FROM sales_history s JOIN categories c ON s.category_id = c.id
            WHERE s.sale_date >= ?
            GROUP BY c.name_ar ORDER BY revenue DESC
        """, (since,)).fetchall()
        top = conn.execute("""
            SELECT product_name, SUM(quantity_sold) as qty, SUM(revenue) as rev
            FROM sales_history WHERE sale_date >= ?
            GROUP BY product_name ORDER BY qty DESC LIMIT 5
        """, (since,)).fetchall()
        return {
            "period_days": days,
            "total_revenue": round(total["rev"], 2),
            "total_units_sold": total["qty"],
            "by_category": [dict(r) for r in by_cat],
            "top_products": [dict(r) for r in top],
        }


def get_low_stock_products(threshold: int = 5) -> List[Dict]:
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT p.*, c.name_ar as category_name
            FROM products p JOIN categories c ON p.category_id = c.id
            WHERE p.stock_count <= ?
            ORDER BY p.stock_count
        """, (threshold,)).fetchall()
        return [dict(r) for r in rows]


def get_top_products(days: int = 30, limit: int = 10) -> List[Dict]:
    with get_connection() as conn:
        since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        rows = conn.execute("""
            SELECT product_name, SUM(quantity_sold) as total_sold,
                   SUM(revenue) as total_revenue, AVG(unit_price) as avg_price
            FROM sales_history WHERE sale_date >= ?
            GROUP BY product_name ORDER BY total_sold DESC LIMIT ?
        """, (since, limit)).fetchall()
        return [dict(r) for r in rows]


def get_product_sales_history(product_id: int, days: int = 90) -> List[Dict]:
    """Get daily sales for a product — used for LLM prediction."""
    with get_connection() as conn:
        since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        rows = conn.execute("""
            SELECT sale_date, SUM(quantity_sold) as qty, SUM(revenue) as revenue
            FROM sales_history WHERE product_id = ? AND sale_date >= ?
            GROUP BY sale_date ORDER BY sale_date
        """, (product_id, since)).fetchall()
        return [dict(r) for r in rows]


def get_category_correlation() -> List[Dict]:
    """Which categories are often bought together (same day)."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT a.product_name as product_a, b.product_name as product_b, COUNT(*) as co_purchases
            FROM orders a JOIN orders b
              ON date(a.created_at) = date(b.created_at)
             AND a.id < b.id
            GROUP BY a.product_name, b.product_name
            ORDER BY co_purchases DESC LIMIT 10
        """).fetchall()
        return [dict(r) for r in rows]


def get_account_summary() -> Dict:
    with get_connection() as conn:
        total_rev = conn.execute("SELECT COALESCE(SUM(revenue),0) as r FROM sales_history").fetchone()["r"]
        total_orders = conn.execute("SELECT COUNT(*) as c FROM orders").fetchone()["c"]
        total_products = conn.execute("SELECT COUNT(*) as c FROM products").fetchone()["c"]
        avg_order = conn.execute("SELECT COALESCE(AVG(total_price),0) as a FROM orders").fetchone()["a"]
        today_rev = conn.execute(
            "SELECT COALESCE(SUM(revenue),0) as r FROM sales_history WHERE sale_date = date('now')"
        ).fetchone()["r"]
        return {
            "total_revenue_egp": round(total_rev, 2),
            "total_orders": total_orders,
            "total_products_in_stock": total_products,
            "average_order_value_egp": round(avg_order, 2),
            "today_revenue_egp": round(today_rev, 2),
        }
