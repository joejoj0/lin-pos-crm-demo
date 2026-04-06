import streamlit as st
import requests
from datetime import datetime

API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="Line POS CRM Demo",
    page_icon="🛒",
    layout="wide"
)

st.title("🛒 Line POS CRM - Client Demo")
st.markdown("*Demo Version - Showcasing Thai Retail Loyalty System*")

# Sidebar navigation
tab1, tab2, tab3, tab4 = st.tabs(["🛍️ POS Checkout", "📦 Products", "👥 Customers", "📊 Reports"])

def get_products():
    """Fetch products from API"""
    try:
        resp = requests.get(f"{API_BASE}/api/products", timeout=5)
        return resp.json()
    except:
        st.error("⚠️ POS API not running. Start with: python pos.py")
        return []

# == TAB 1: POS CHECKOUT ==
with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🛍️ Add Items to Cart")
        
        # Select product
        products = get_products()
        product_options = {p['name']: p for p in products}
        
        if product_options:
            selected_product = st.selectbox("Product", list(product_options.keys()))
            
            if selected_product:
                product = product_options[selected_product]
                col_a, col_b = st.columns(2)
                with col_a:
                    qty = st.number_input("Quantity", min_value=1, max_value=100, value=1)
                with col_b:
                    st.info(f"Price: ฿{product['price']:.2f}")
                
                if st.button("➕ Add to Cart"):
                    if 'cart' not in st.session_state:
                        st.session_state.cart = []
                    
                    # Check if product already in cart
                    existing_item = next((item for item in st.session_state.cart if item['product_id'] == product['product_id']), None)
                    
                    if existing_item:
                        existing_item['quantity'] += qty
                    else:
                        st.session_state.cart.append({
                            'product_id': product['product_id'],
                            'product_name': product['name'],
                            'unit_price': product['price'],
                            'quantity': qty,
                            'subtotal': product['price'] * qty
                        })
                    
                    st.success(f"✓ {qty}x {product['name']} added")
        else:
            st.warning("No products in catalog")
    
    with col2:
        st.subheader("📋 Cart")
        
        if 'cart' in st.session_state and st.session_state.cart:
            for i, item in enumerate(st.session_state.cart):
                st.markdown(f"**{item['product_name']}**")
                st.write(f"Qty: {item['quantity']} × ฿{item['unit_price']:.2f}")
                st.write(f"Subtotal: ฿{item['subtotal']:.2f}")
                if st.button(f"🗑️ Remove", key=f"remove_{i}"):
                    st.session_state.cart.pop(i)
            
            # Customer info
            st.markdown("---")
            st.markdown("**👤 Customer**")
            
            customer_line = st.text_input("Line ID (optional)", placeholder="LINE12345ABC")
            customer_name = st.text_input("Customer Name (optional)")
            
            # Payment method
            st.markdown("---")
            payment_method = st.selectbox("Payment Method", ["cash", "card", "line_pay"])
            
            # Calculate total
            cart_total = sum(item['subtotal'] for item in st.session_state.cart)
            st.markdown(f"**💰 Total: ฿{cart_total:.2f}**")
            
            if st.button("✅ Process Transaction", type="primary", use_container_width=True):
                if not customer_line and not customer_name:
                    st.warning("⚠️ Please enter customer info (or scan QR)")
                else:
                    # Send to API
                    payload = {
                        "customer_line_id": customer_line if customer_line else None,
                        "items": st.session_state.cart,
                        "payment_method": payment_method
                    }
                    
                    try:
                        resp = requests.post(f"{API_BASE}/api/transactions", json=payload, timeout=5)
                        result = resp.json()
                        
                        if 'points_earned' in result:
                            st.success(f"✅ Transaction complete!")
                            st.balloons()
                            st.metric("Points Earned", f"{result['points_earned']} pts")
                            if result.get('tier_upgraded'):
                                st.success(f"🎉 Tier upgraded to {result['new_tier'].upper()}!")
                        else:
                            st.error("❌ Transaction failed")
                            
                    except Exception as e:
                        st.error(f"API Error: {str(e)}")
                    
                    st.session_state.cart = []
        else:
            st.info("👈 Add items to cart from left panel")

# == TAB 2: PRODUCTS ==
with tab2:
    st.subheader("📦 Product Catalog")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.expander("➕ Add New Product"):
            new_sku = st.text_input("SKU")
            new_barcode = st.text_input("Barcode")
            new_name = st.text_input("Product Name")
            new_price = st.number_input("Price (฿)", min_value=0.0, step=1.0)
            new_category = st.text_input("Category")
            
            if st.button("Add Product"):
                try:
                    payload = {
                        "sku": new_sku,
                        "barcode": new_barcode,
                        "name": new_name,
                        "price": new_price,
                        "category": new_category
                    }
                    resp = requests.post(f"{API_BASE}/api/products", json=payload, timeout=5)
                    if resp.status_code == 200:
                        st.success("✓ Product added!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to add product")
                except Exception as e:
                    st.error(f"API Error: {str(e)}")
    
    with col2:
        products = get_products()
        
        st.markdown("**Current Products:**")
        for product in products:
            col_a, col_b, col_c = st.columns([2, 1, 1])
            with col_a:
                st.write(f"**{product['name']}**")
            with col_b:
                st.write(f"฿{product['price']:.2f}")
            with col_c:
                st.write(f"Stock: {product['inventory_quantity']}")

# == TAB 3: CUSTOMERS ==
with tab3:
    st.subheader("👥 Loyalty Customers")
    
    # Search by Line ID
    search_line = st.text_input("🔍 Search by Line ID", placeholder="LINE...")
    
    if search_line:
        try:
            resp = requests.get(f"{API_BASE}/api/customers/line/{search_line}", timeout=5)
            if resp.status_code == 200:
                customer = resp.json()
                
                st.markdown(f"**{customer['name']}**")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Line ID", customer.get('line_id', 'N/A'))
                col2.metric("Tier", customer['tier'].upper())
                col3.metric("Points", f"{customer['total_points']} pts")
                col4.metric("Total Spent", f"฿{customer['total_spent']:.0f}")
                
                st.write(f"**Purchases:** {customer['total_purchases']} | **Last Visit:** {customer['last_purchase_date']}")
                
            else:
                st.warning("Customer not found")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    else:
        st.info("Enter a Line ID to view customer profile")
    
    st.markdown("---")
    st.markdown("**🎯 Tier Benefits:**")
    st.markdown("""
    - **Bronze**: 1 point per ฿10
    - **Silver**: 1.2 points per ฿10 (15k+ spent)
    - **Gold**: 1.5 points per ฿10 (50k+ spent)
    """)

# == TAB 4: REPORTS ==
with tab4:
    st.subheader("📊 Sales Reports")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Recent Transactions:**")
        try:
            resp = requests.get(f"{API_BASE}/api/transactions/recent", params={"limit": 10}, timeout=5)
            transactions = resp.json()
            
            for txn in transactions:
                col_a, col_b = st.columns([2, 1])
                with col_a:
                    st.markdown(f"**#{txn['transaction_id']}** | {txn.get('customer_name', 'Guest')}")
                with col_b:
                    st.write(f"฿{txn['total_amount']:.2f}")
        except Exception as e:
            st.error(f"Error loading transactions: {str(e)}")
    
    with col2:
        st.markdown("**Demo Statistics:**")
        stats = {
            "Total Products": 20,
            "Active Customers": 3,
            "Avg Transaction": "฿2,100",
            "Retention Rate": "45%"
        }
        for key, value in stats.items():
            st.metric(key, value)
