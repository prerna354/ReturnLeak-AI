import os
import pandas as pd
import numpy as np

def run_analysis():
    print("==========================================================================")
    print("         RETURNLEAK AI: EXECUTIVE DATA ANALYSIS PIPELINE                 ")
    print("==========================================================================")
    
    # Load Data
    data_dir = 'data'
    if not os.path.exists(os.path.join(data_dir, 'returns.csv')):
        print("Dataset missing! Run 'python generate_data.py' first.")
        return

    sellers = pd.read_csv(f'{data_dir}/sellers.csv')
    products = pd.read_csv(f'{data_dir}/products.csv')
    customers = pd.read_csv(f'{data_dir}/customers.csv')
    orders = pd.read_csv(f'{data_dir}/orders.csv')
    order_items = pd.read_csv(f'{data_dir}/order_items.csv')
    returns = pd.read_csv(f'{data_dir}/returns.csv')

    # Merge Data
    full_df = order_items.merge(orders, on='order_id') \
                         .merge(products, on='product_id') \
                         .merge(sellers, on='seller_id') \
                         .merge(customers, on='customer_id') \
                         .merge(returns, on='item_id', how='left')

    # 1. Macro KPIs
    total_sales_value = full_df['total_item_value'].sum()
    total_returns = full_df['return_id'].notnull().sum()
    total_return_rate = (total_returns / len(full_df)) * 100
    total_refund_value = full_df['refund_amount'].sum()
    total_logistics_loss = full_df['reverse_logistics_cost'].sum()
    scrapped_loss = full_df[full_df['restockable'] == 0]['total_item_value'].sum()
    total_leakage = total_logistics_loss + scrapped_loss

    print("\n--- 1. MACRO FINANCIAL METRICS ---")
    print(f"Gross Merchandise Value (GMV) : ${total_sales_value:,.2f}")
    print(f"Total Order Items Processed   : {len(full_df):,}")
    print(f"Total Return Count            : {total_returns:,}")
    print(f"Overall Return Rate           : {total_return_rate:.2f}%")
    print(f"Gross Refunds Processed        : ${total_refund_value:,.2f}")
    print(f"Reverse Logistics Cost Loss   : ${total_logistics_loss:,.2f}")
    print(f"Scrapped Inventory Loss       : ${scrapped_loss:,.2f}")
    print(f"TOTAL NET REVENUE LEAKAGE     : ${total_leakage:,.2f}")

    # 2. Category Driver Analysis
    print("\n--- 2. CATEGORY LEAKAGE BREAKDOWN ---")
    cat_summary = full_df.groupby('category').agg(
        Total_Items=('item_id', 'count'),
        Returns=('return_id', 'count'),
        Gross_Sales=('total_item_value', 'sum'),
        Refunds=('refund_amount', 'sum'),
        Logistics_Loss=('reverse_logistics_cost', 'sum')
    ).reset_index()
    
    cat_summary['Return_Rate_%'] = (cat_summary['Returns'] / cat_summary['Total_Items']) * 100
    cat_summary['Leakage_Share_%'] = (cat_summary['Logistics_Loss'] / total_logistics_loss) * 100
    cat_summary = cat_summary.sort_values(by='Logistics_Loss', ascending=False)
    print(cat_summary[['category', 'Total_Items', 'Returns', 'Return_Rate_%', 'Logistics_Loss', 'Leakage_Share_%']].to_string(index=False))

    # 3. Seller Defect Detection & Outliers
    print("\n--- 3. TOP 5 HIGH-RISK LEAKAGE SELLERS ---")
    seller_summary = full_df.groupby(['seller_id', 'seller_name', 'seller_type']).agg(
        Units_Sold=('item_id', 'count'),
        Defect_Returns=('return_reason', lambda x: (x.isin(['Defective', 'Damaged in Transit'])).sum()),
        Total_Logistics_Loss=('reverse_logistics_cost', 'sum')
    ).reset_index()
    
    seller_summary['Defect_Rate_%'] = (seller_summary['Defect_Returns'] / seller_summary['Units_Sold']) * 100
    top_problem_sellers = seller_summary.sort_values(by='Total_Logistics_Loss', ascending=False).head(5)
    print(top_problem_sellers[['seller_id', 'seller_name', 'seller_type', 'Units_Sold', 'Defect_Rate_%', 'Total_Logistics_Loss']].to_string(index=False))

    # 4. Projected Impact of Mitigations
    print("\n--- 4. RETURNLEAK AI MITIGATION IMPACT SIMULATION ---")
    # Action 1: Enforce quality threshold on top 5% defect sellers
    seller_leak_mitigation = top_problem_sellers['Total_Logistics_Loss'].sum() * 0.60
    # Action 2: Apparel Sizing Chart Precision optimization (saving 25% on sizing returns)
    apparel_sizing_loss = full_df[full_df['return_reason'] == 'Sizing Issues']['reverse_logistics_cost'].sum()
    sizing_mitigation = apparel_sizing_loss * 0.25
    
    total_projected_savings = seller_leak_mitigation + sizing_mitigation
    projected_leakage_reduction_pct = (total_projected_savings / total_leakage) * 100

    print(f"Projected Savings via Seller Offboarding/Audits : ${seller_leak_mitigation:,.2f}")
    print(f"Projected Savings via Apparel Sizing Fit Model  : ${sizing_mitigation:,.2f}")
    print(f"TOTAL POTENTIAL ANNUAL LEAK RECOVERY             : ${total_projected_savings:,.2f}")
    print(f"PROJECTED NET FINANCIAL LEAKAGE REDUCTION        : {projected_leakage_reduction_pct:.2f}%")
    print("==========================================================================")

if __name__ == '__main__':
    run_analysis()