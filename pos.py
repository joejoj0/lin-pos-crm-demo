from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
import database
from datetime import datetime

app = FastAPI(title="Line POS CRM API", version="1.0.0")

# Enable CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ProductCreate(BaseModel):
    sku: str
    barcode: Optional[str]
    name: str
    price: float
    category: Optional[str]

class Item(BaseModel):
    product_id: int
    quantity: int
    unit_price: float

class TransactionCreate(BaseModel):
    customer_line_id: Optional[str]
    items: List[Item]
    payment_method: str = "cash"

class CustomerCreate(BaseModel):
    line_id: str
    name: str
    phone: str

@app.on_event("startup")
async def startup():
    """Initialize database on startup"""
    database.init_database()

# Products endpoints
@app.get("/api/products", response_model=List[dict])
async def get_products():
    """Get all active products"""
    return database.get_all_products()

@app.post("/api/products", response_model=dict)
async def add_product(product: ProductCreate):
    """Add new product to catalog"""
    conn = database.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO products (sku, barcode, name, price, category)
            VALUES (?, ?, ?, ?, ?)
        ''', (product.sku, product.barcode, product.name, product.price, product.category))
        product_id = cursor.lastrowid
        conn.commit()
        return {"success": True, "product_id": product_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

# Customer endpoints
@app.get("/api/customers/line/{line_id}", response_model=dict)
async def get_customer(line_id: str):
    """Get customer by Line ID"""
    customer = database.get_customer_by_line(line_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@app.post("/api/customers", response_model=dict)
async def create_customer(customer: CustomerCreate):
    """Create new customer linked to Line OA"""
    existing = database.get_customer_by_line(customer.line_id)
    if existing:
        return existing
    
    return database.add_customer(customer.line_id, customer.name, customer.phone)

# Transaction endpoints
@app.post("/api/transactions", response_model=dict)
async def process_transaction(transaction: TransactionCreate):
    """Process transaction and calculate loyalty points"""
    try:
        items = [{"product_id": i.product_id, "quantity": i.quantity, "unit_price": i.unit_price} for i in transaction.items]
        result = database.create_transaction(
            customer_line_id=transaction.customer_line_id,
            items=items,
            payment_method=transaction.payment_method
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/transactions/recent", response_model=List[dict])
async def get_recent_transactions(limit: int = 10):
    """Get recent transactions"""
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT t.*, c.name as customer_name, c.line_id
        FROM transactions t
        LEFT JOIN customers c ON t.customer_id = c.customer_id
        ORDER BY t.created_at DESC
        LIMIT ?
    ''', (limit,))
    transactions = cursor.fetchall()
    conn.close()
    return [dict(row) for row in transactions]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
