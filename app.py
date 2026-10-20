import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(
    page_title="ReturnLeak AI — Dashboard",
    page_icon="📉",
    layout="wide"
)

@st.cache_data
def load_data():
    if not os.path.exists('data/returns.csv'):
        st.error("Data files not found. Please run `python generate_data.py` first.")
        st.stop()
        
    sellers = pd.read_csv('data/sellers.csv')
    products = pd.read_csv('data/products.csv')
    customers = pd.read_csv('data/customers.csv')
    orders = pd.read_csv('data/orders.csv')
    order_items = pd.read_csv('data/order_items.csv')
    returns = pd.read_csv('data/returns.csv')

    df = order_items.merge(orders, on='order_id') \
                    .merge(products, on='product_id') \
                    .merge(sellers, on='seller_id') \
                    .merge(customers, on='customer_id') \
                    .merge(returns, on='item_id', how='left')
    return df

df = load_data()

# Sidebar Controls
st.sidebar.title("🔍 Filter Analysis")
selected_region = st.sidebar.multiselect("Select Region", options=df['region'].unique(), default=df['region'].unique())
selected_category = st.sidebar.multiselect("Select Category", options=df['category'].unique(), default=df['category'].unique())

filtered_df = df[(df['region'].isin(selected_region)) & (df['category'].isin(selected_category))]

# Main Layout
st.title("📉 ReturnLeak AI: E-Commerce Return Loss Detection")
st.markdown("### Strategic Intelligence Platform isolating Root Causes of Reverse Logistics Loss")

# Top Level KPIs
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
total_gross = filtered_df['total_item_value'].sum()
total_returns_cnt = filtered_df['return_id'].notnull().sum()
return_rate = (total_returns_cnt / len(filtered_df)) * 100 if len(filtered_df) > 0 else 0
total_leakage = filtered_df['reverse_logistics_cost'].sum() + filtered_df[filtered_df['restockable'] == 0]['total_item_value'].sum()

kpi1.metric("Gross Merchandise Value", f"${total_gross:,.2f}")
kpi2.metric("Total Return Events", f"{total_returns_cnt:,}")
kpi3.metric("Overall Return Rate", f"{return_rate:.2f}%")
kpi4.metric("Net Financial Leakage", f"${total_leakage:,.2f}", delta="-Leakage", delta_color="inverse")

st.markdown("---")

# Visual Charts Layout
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📦 Financial Leakage by Product Category")
    cat_leak = filtered_df.groupby('category')['reverse_logistics_cost'].sum().reset_index()
    fig_cat = px.bar(
        cat_leak, 
        x='category', 
        y='reverse_logistics_cost',
        labels={'reverse_logistics_cost': 'Reverse Logistics Loss ($)', 'category': 'Category'},
        color='reverse_logistics_cost',
        color_continuous_scale='Reds'
    )
    st.plotly_chart(fig_cat, use_container_width=True)

with col_right:
    st.subheader("❓ Primary Reasons for Returns")
    reason_df = filtered_df['return_reason'].value_counts().reset_index()
    reason_df.columns = ['reason', 'count']
    fig_reason = px.pie(
        reason_df, 
        names='reason', 
        values='count', 
        hole=0.4,
        color_discrete_sequence=px.colors.sequential.RdBu
    )
    st.plotly_chart(fig_reason, use_container_width=True)

# Seller Performance & Defect Matrix
st.subheader("⚠️ High Defect Seller Pareto Analysis")
seller_perf = filtered_df.groupby(['seller_id', 'seller_name']).agg(
    Sold=('item_id', 'count'),
    Returned=('return_id', 'count'),
    Loss=('reverse_logistics_cost', 'sum')
).reset_index()

seller_perf['Return_Rate_%'] = (seller_perf['Returned'] / seller_perf['Sold']) * 100
seller_perf = seller_perf.sort_values(by='Loss', ascending=False).head(10)

fig_seller = px.scatter(
    seller_perf,
    x='Sold',
    y='Return_Rate_%',
    size='Loss',
    color='seller_name',
    hover_name='seller_name',
    title="Top 10 Leakage Sellers (Bubble Size = Net Financial Loss)"
)
st.plotly_chart(fig_seller, use_container_width=True)

# Raw Data Inspection
if st.checkbox("Show Detailed Raw Leakage Audit Data"):
    st.dataframe(filtered_df[['order_id', 'seller_name', 'category', 'total_item_value', 'return_reason', 'reverse_logistics_cost']].dropna(subset=['return_reason']))