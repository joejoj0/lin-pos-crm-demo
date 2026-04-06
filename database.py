import sqlite3
from datetime import datetime, date

DATABASE = 'linepos.db'

def get_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize database with schema and sample data"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create tables
    cursor.executescript('''
    -- Products table
    CREATE TABLE IF NOT EXISTS products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        sku TEXT UNIQUE NOT NULL,
        barcode TEXT,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        category TEXT,
        inventory_quantity INTEGER DEFAULT 100,
        status TEXT DEFAULT 'active'
    );
    
    -- Customers table (linked to Line OA)
    CREATE TABLE IF NOT EXISTS customers (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        line_id TEXT UNIQUE,
        name TEXT,
        phone TEXT,
        registration_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        total_spent REAL DEFAULT 0,
        total_purchases INTEGER DEFAULT 0,
        last_purchase_date DATE,
        tier TEXT DEFAULT 'bronze' CHECK(tier IN ('bronze', 'silver', 'gold')),
        tier_earned_date DATE,
        total_points REAL DEFAULT 0
    );
    
    -- Transactions table
    CREATE TABLE IF NOT EXISTS transactions (
        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        total_amount REAL NOT NULL,
        payment_method TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    );
    
    -- Transaction items
    CREATE TABLE IF NOT EXISTS transaction_items (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        subtotal REAL NOT NULL,
        FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    );
    
    -- Loyalty points log
    CREATE TABLE IF NOT EXISTS loyalty_points (
        point_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        transaction_id INTEGER NOT NULL,
        points_earned INTEGER DEFAULT 0,
        points_redeemed INTEGER DEFAULT 0,
        net_change INTEGER NOT NULL,
        transaction_type TEXT CHECK(transaction_type IN ('earn', 'redeem')),
        points_balance REAL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
        FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id)
    );
    ''')
    
    conn.commit()
    print("✓ Database initialized")
    
    # Seed sample products
    seed_sample_products(cursor)
    
    # Seed sample customers
    seed_sample_customers(cursor)
    
    conn.commit()
    print("✓ Sample data loaded")
    conn.close()

def seed_sample_products(cursor):
    """Seed 20 sample products for demo"""
    products = [
        ('SKU001', 'BAR001', 'Coffee Bean 1kg', 450.00, 'Beverages', 50),
        ('SKU002', 'BAR002', 'Thai Tea Mix 500g', 120.00, 'Beverages', 100),
        ('SKU003', 'BAR003', 'Rice Khao Hom Mali 5kg', 280.00, 'Rice', 30),
        ('SKU004', 'BAR004', 'Instant Noodles 5 pack', 45.00, 'Snacks', 200),
        ('SKU005', 'BAR005', 'Fish Sauce 700ml', 65.00, 'Condiments', 80),
        ('SKU006', 'BAR006', 'Soy Sauce 700ml', 70.00, 'Condiments', 80),
        ('SKU007', 'BAR007', 'Oyster Sauce 500ml', 80.00, 'Condiments', 60),
        ('SKU008', 'BAR008', 'Palm Sugar 1kg', 55.00, 'Baking', 70),
        ('SKU009', 'BAR009', 'Coconut Milk 400ml', 40.00, 'Dairy', 150),
        ('SKU010', 'BAR010', 'Green Curry Paste 250g', 85.00, 'Condiments', 90),
        ('SKU011', 'BAR011', 'Red Curry Paste 250g', 85.00, 'Condiments', 90),
        ('SKU012', 'BAR012', 'Jasmine Rice 1kg', 65.00, 'Rice', 100),
        ('SKU013', 'BAR013', 'Coconut Milk 1L', 50.00, 'Dairy', 120),
        ('SKU014', 'BAR014', 'Chili Flakes 100g', 75.00, 'Spices', 60),
        ('SKU015', 'BAR015', 'Shrimp Paste 100g', 95.00, 'Condiments', 40),
        ('SKU016', 'BAR016', 'Tamarind Paste 500g', 70.00, 'Condiments', 50),
        ('SKU017', 'BAR017', 'Lemongrass Fresh 100g', 35.00, 'Fresh Herbs', 80),
        ('SKU018', 'BAR018', 'Galangal Fresh 200g', 40.00, 'Fresh Herbs', 70),
        ('SKU019', 'BAR019', 'Kaffir Lime Leaves 50g', 55.00, 'Fresh Herbs', 60),
        ('SKU020', 'BAR020', 'Thai Basil Fresh 100g', 30.00, 'Fresh Herbs', 100),
    ]
    
    cursor.executemany('''
        INSERT OR REPLACE INTO products (sku, barcode, name, price, category, inventory_quantity)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', products)
    print("✓ 20 products seeded")

def seed_sample_customers(cursor):
    """Seed 3 sample customers for demo"""
    customers = [
        ('LINE12345ABC', 'Siriporn Thanakit', '0812345678', 15000.00, 35, '2026-03-01', 'gold', '2026-03-15', 1500.00),
        ('LINE67890XYZ', 'James Wilson', '0823456789', 8500.00, 18, '2026-03-10', 'silver', '2026-03-25', 850.00),
        ('LINE11111TEST', 'Somchai Jaidee', '0834567890', 2500.00, 8, '2026-03-20', 'bronze', '2026-04-01', 250.00),
    ]
    
    cursor.executemany('''
        INSERT OR REPLACE INTO customers (line_id, name, phone, total_spent, total_purchases, last_purchase_date, tier, tier_earned_date, total_points)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', customers)
    print("✓ 3 customers seeded")

# API Functions
def get_all_products():
    """Get all active products"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE status='active' ORDER BY name")
    products = cursor.fetchall()
    conn.close()
    return [dict(row) for row in products]

def get_customer_by_line(line_id: str):
    """Get customer by Line ID"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers WHERE line_id = ?", (line_id,))
    customer = cursor.fetchone()
    conn.close()
    return dict(customer) if customer else None

def add_customer(line_id: str, name: str, phone: str) -> dict:
    """Create new customer (linked to Line OA)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Insert new customer
    cursor.execute('''
        INSERT INTO customers (line_id, name, phone)
        VALUES (?, ?, ?)
    ''', (line_id, name, phone))
    
    customer_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return get_customer_by_line(line_id)

def create_transaction(customer_line_id: str, items: list, payment_method: str = 'cash') -> dict:
    """Process a transaction and calculate loyalty points"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get customer
    customer = get_customer_by_line(customer_line_id)
    customer_id = customer['customer_id'] if customer else None
    
    # Calculate total
    total = sum(item['quantity'] * item['unit_price'] for item in items)
    
    # Insert transaction
    cursor.execute('''
        INSERT INTO transactions (customer_id, total_amount, payment_method)
        VALUES (?, ?, ?)
    ''', (customer_id, total, payment_method))
    
    transaction_id = cursor.lastrowid
    
    # Insert line items
    for item in items:
        cursor.execute('''
            INSERT INTO transaction_items (transaction_id, product_id, quantity, unit_price, subtotal)
            VALUES (?, ?, ?, ?, ?)
        ''', (transaction_id, item['product_id'], item['quantity'], item['unit_price'], item['quantity'] * item['unit_price']))
    
    # Update customer stats
    if customer_id:
        new_total = customer['total_spent'] + total
        new_purchases = customer['total_purchases'] + 1
        
        # Calculate points earned
        points_earned = calculate_loyalty_points(total, customer['tier'])
        
        # Check for tier upgrade
        new_tier = get_tier_from_total(new_total)
        tier_upgraded = new_tier != customer['tier']
        
        cursor.execute('''
            UPDATE customers 
            SET total_spent = ?, total_purchases = ?, last_purchase_date = ?, tier = ?, tier_earned_date = ?
            WHERE customer_id = ?
        ''', (new_total, new_purchases, date.today().isoformat(), new_tier, date.today().isoformat() if tier_upgraded else customer['tier_earned_date'], customer_id))
        
        # Log points
        cursor.execute('''
            INSERT INTO loyalty_points (customer_id, transaction_id, points_earned, transaction_type, points_balance)
            VALUES (?, ?, ?, ?, ?)
        ''', (customer_id, transaction_id, points_earned, 'earn', customer['total_points'] + points_earned))
    
    conn.commit()
    conn.close()
    
    return {
        'transaction_id': transaction_id,
        'customer_id': customer_id,
        'total': total,
        'points_earned': calculate_loyalty_points(total, customer['tier']) if customer else 0,
        'tier_upgraded': tier_upgraded if customer else False,
        'new_tier': get_tier_from_total(customer['total_spent'] + total) if customer else 'bronze'
    }

def calculate_loyalty_points(total_spent: float, tier: str) -> int:
    """Calculate points earned based on spend and tier"""
    base_rate = 0.1  # 1 point per ฿10
    multipliers = {'bronze': 1.0, 'silver': 1.2, 'gold': 1.5}
    return int(total_spent * base_rate * multipliers.get(tier, 1.0))

def get_tier_from_total(total_spent: float) -> str:
    """Determine tier based on total spending"""
    if total_spent >= 50000:
        return 'gold'
    elif total_spent >= 10000:
        return 'silver'
    else:
        return 'bronze'
