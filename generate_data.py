import os
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

def generate_ecommerce_data():
    print("Generating ReturnLeak AI dataset (>50,000 records)...")
    
    # 1. Sellers (500 records)
    sellers = []
    seller_types = ['Authorized', 'Third-Party', 'Wholesale', 'Direct Brand']
    for i in range(1, 501):
        # 5% of sellers are intentionally injected with high defect rates
        is_problematic = (i % 20 == 0)
        base_defect_rate = np.random.uniform(0.12, 0.28) if is_problematic else np.random.uniform(0.01, 0.05)
        sellers.append({
            'seller_id': f"SEL-{i:04d}",
            'seller_name': f"Seller_{i}",
            'seller_type': random.choice(seller_types),
            'rating': round(np.random.uniform(2.5, 3.8) if is_problematic else np.random.uniform(3.9, 5.0), 2),
            'historical_defect_rate': round(base_defect_rate, 4),
            'created_at': datetime(2023, 1, 1) + timedelta(days=random.randint(0, 365))
        })
    df_sellers = pd.DataFrame(sellers)

    # 2. Products (2,500 records)
    categories = {
        'Apparel': ['Sizing Issues', 'Material Dislike', 'Wrong Item Sent', 'Defective'],
        'Electronics': ['Defective', 'Missing Accessories', 'Did Not Work', 'Buyer Remorse'],
        'Home & Kitchen': ['Damaged in Transit', 'Defective', 'Size Mismatch'],
        'Footwear': ['Sizing Issues', 'Uncomfortable', 'Defective'],
        'Beauty': ['Expired', 'Allergic Reaction', 'Wrong Item Sent']
    }
    
    products = []
    for i in range(1, 2501):
        category = random.choice(list(categories.keys()))
        seller = df_sellers.sample(1).iloc[0]
        base_price = round(float(np.random.uniform(15.0, 450.0)), 2)
        
        products.append({
            'product_id': f"PROD-{i:05d}",
            'product_name': f"{category} Item {i}",
            'category': category,
            'unit_price': base_price,
            'cost_price': round(base_price * np.random.uniform(0.4, 0.65), 2),
            'seller_id': seller['seller_id'],
            'is_high_risk_category': 1 if category in ['Apparel', 'Electronics'] else 0
        })
    df_products = pd.DataFrame(products)

    # 3. Customers (5,000 records)
    regions = ['North America', 'Europe', 'Asia-Pacific', 'Latin America']
    customers = []
    for i in range(1, 5001):
        customers.append({
            'customer_id': f"CUST-{i:05d}",
            'region': random.choice(regions),
            'loyalty_tier': random.choices(['Bronze', 'Silver', 'Gold', 'Platinum'], weights=[0.5, 0.3, 0.15, 0.05])[0],
            'signup_date': datetime(2023, 1, 1) + timedelta(days=random.randint(0, 500))
        })
    df_customers = pd.DataFrame(customers)

    # 4. Orders (20,000 records)
    orders = []
    start_date = datetime(2024, 1, 1)
    for i in range(1, 20001):
        cust = df_customers.sample(1).iloc[0]
        order_date = start_date + timedelta(days=random.randint(0, 270), hours=random.randint(0, 23))
        orders.append({
            'order_id': f"ORD-{i:06d}",
            'customer_id': cust['customer_id'],
            'order_date': order_date.strftime('%Y-%m-%d %H:%M:%S'),
            'shipping_cost': round(float(np.random.uniform(5.0, 25.0)), 2),
            'payment_method': random.choice(['Credit Card', 'PayPal', 'UPI', 'BNPL'])
        })
    df_orders = pd.DataFrame(orders)

    # 5. Order Items (~35,000 records)
    order_items = []
    item_id_counter = 1
    for _, order in df_orders.iterrows():
        num_items = random.choices([1, 2, 3, 4], weights=[0.6, 0.25, 0.1, 0.05])[0]
        selected_prods = df_products.sample(num_items)
        for _, prod in selected_prods.iterrows():
            qty = random.randint(1, 3)
            order_items.append({
                'item_id': f"ITM-{item_id_counter:07d}",
                'order_id': order['order_id'],
                'product_id': prod['product_id'],
                'quantity': qty,
                'item_price': prod['unit_price'],
                'total_item_value': round(prod['unit_price'] * qty, 2)
            })
            item_id_counter += 1
    df_order_items = pd.DataFrame(order_items)

    # 6. Returns (~8,000 - 10,000 records injected with specific leak patterns)
    returns = []
    return_id_counter = 1
    
    # Merge order items with products and sellers to calibrate return probability
    merged_items = df_order_items.merge(df_products, on='product_id')
    merged_items = merged_items.merge(df_sellers[['seller_id', 'historical_defect_rate']], on='seller_id')
    
    for _, item in merged_items.iterrows():
        # Inject return drivers:
        # Category risk + Seller defect history
        prob_return = 0.08
        if item['category'] == 'Apparel':
            prob_return += 0.18  # Sizing mismatch leak
        elif item['category'] == 'Electronics':
            prob_return += 0.10
            
        prob_return += item['historical_defect_rate'] * 0.8
        
        if random.random() < prob_return:
            return_reason = random.choice(categories[item['category']])
            return_date = datetime.strptime(
                df_orders.loc[df_orders['order_id'] == item['order_id'], 'order_date'].values[0],
                '%Y-%m-%d %H:%M:%S'
            ) + timedelta(days=random.randint(2, 14))
            
            # Logistics/restocking costs based on reason
            reverse_logistics_cost = round(float(np.random.uniform(8.0, 30.0)), 2)
            restockable = 0 if return_reason in ['Defective', 'Damaged in Transit', 'Expired'] else 1
            
            returns.append({
                'return_id': f"RET-{return_id_counter:06d}",
                'item_id': item['item_id'],
                'return_date': return_date.strftime('%Y-%m-%d %H:%M:%S'),
                'return_reason': return_reason,
                'refund_amount': item['total_item_value'],
                'reverse_logistics_cost': reverse_logistics_cost,
                'restockable': restockable
            })
            return_id_counter += 1

    df_returns = pd.DataFrame(returns)

    # Ensure output directory exists
    os.makedirs('data', exist_ok=True)
    
    # Save datasets
    df_sellers.to_csv('data/sellers.csv', index=False)
    df_products.to_csv('data/products.csv', index=False)
    df_customers.to_csv('data/customers.csv', index=False)
    df_orders.to_csv('data/orders.csv', index=False)
    df_order_items.to_csv('data/order_items.csv', index=False)
    df_returns.to_csv('data/returns.csv', index=False)

    print("Data generation complete. Saved to 'data/' directory.")
    print(f"Total Rows Generated: {len(df_sellers) + len(df_products) + len(df_customers) + len(df_orders) + len(df_order_items) + len(df_returns):,}")

if __name__ == '__main__':
    generate_ecommerce_data()