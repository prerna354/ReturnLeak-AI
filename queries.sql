-- Schema Setup for ReturnLeak AI
DROP TABLE IF EXISTS returns CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS sellers CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

CREATE TABLE sellers (
    seller_id VARCHAR(20) PRIMARY KEY,
    seller_name VARCHAR(100),
    seller_type VARCHAR(50),
    rating NUMERIC(3,2),
    historical_defect_rate NUMERIC(5,4),
    created_at TIMESTAMP
);

CREATE TABLE products (
    product_id VARCHAR(20) PRIMARY KEY,
    product_name VARCHAR(150),
    category VARCHAR(50),
    unit_price NUMERIC(10,2),
    cost_price NUMERIC(10,2),
    seller_id VARCHAR(20) REFERENCES sellers(seller_id),
    is_high_risk_category INT
);

CREATE TABLE customers (
    customer_id VARCHAR(20) PRIMARY KEY,
    region VARCHAR(50),
    loyalty_tier VARCHAR(20),
    signup_date TIMESTAMP
);

CREATE TABLE orders (
    order_id VARCHAR(20) PRIMARY KEY,
    customer_id VARCHAR(20) REFERENCES customers(customer_id),
    order_date TIMESTAMP,
    shipping_cost NUMERIC(10,2),
    payment_method VARCHAR(30)
);

CREATE TABLE order_items (
    item_id VARCHAR(20) PRIMARY KEY,
    order_id VARCHAR(20) REFERENCES orders(order_id),
    product_id VARCHAR(20) REFERENCES products(product_id),
    quantity INT,
    item_price NUMERIC(10,2),
    total_item_value NUMERIC(10,2)
);

CREATE TABLE returns (
    return_id VARCHAR(20) PRIMARY KEY,
    item_id VARCHAR(20) REFERENCES order_items(item_id),
    return_date TIMESTAMP,
    return_reason VARCHAR(100),
    refund_amount NUMERIC(10,2),
    reverse_logistics_cost NUMERIC(10,2),
    restockable INT
);

-- ============================================================================
-- QUERY 1: Financial Impact & Total Leakage by Category (34% Driver Breakdown)
-- ============================================================================
WITH GrossSales AS (
    SELECT 
        p.category,
        SUM(oi.total_item_value) AS gross_revenue,
        COUNT(DISTINCT oi.item_id) AS total_items_sold
    FROM order_items oi
    JOIN products p ON oi.product_id = p.product_id
    GROUP BY p.category
),
ReturnLeakage AS (
    SELECT 
        p.category,
        COUNT(DISTINCT r.return_id) AS returned_items_count,
        SUM(r.refund_amount) AS total_refunded_amount,
        SUM(r.reverse_logistics_cost) AS total_reverse_shipping_loss,
        SUM(CASE WHEN r.restockable = 0 THEN oi.total_item_value ELSE 0 END) AS scrapped_inventory_loss
    FROM returns r
    JOIN order_items oi ON r.item_id = oi.item_id
    JOIN products p ON oi.product_id = p.product_id
    GROUP BY p.category
)
SELECT 
    gs.category,
    gs.gross_revenue,
    COALESCE(rl.returned_items_count, 0) AS returned_items_count,
    ROUND((COALESCE(rl.returned_items_count, 0)::NUMERIC / gs.total_items_sold) * 100, 2) AS return_rate_pct,
    COALESCE(rl.total_refunded_amount, 0) AS total_refunds,
    COALESCE(rl.total_reverse_shipping_loss, 0) AS reverse_logistics_cost,
    COALESCE(rl.scrapped_inventory_loss, 0) AS scrapped_inventory_cost,
    (COALESCE(rl.total_reverse_shipping_loss, 0) + COALESCE(rl.scrapped_inventory_loss, 0)) AS total_net_financial_leakage,
    ROUND(
        ((COALESCE(rl.total_reverse_shipping_loss, 0) + COALESCE(rl.scrapped_inventory_loss, 0)) / 
        SUM(COALESCE(rl.total_reverse_shipping_loss, 0) + COALESCE(rl.scrapped_inventory_loss, 0)) OVER ()) * 100, 
        2
    ) AS percent_contribution_to_total_leakage
FROM GrossSales gs
LEFT JOIN ReturnLeakage rl ON gs.category = rl.category
ORDER BY total_net_financial_leakage DESC;

-- ============================================================================
-- QUERY 2: Seller Defect Pareto Ranking using Window Functions
-- ============================================================================
WITH SellerMetrics AS (
    SELECT 
        s.seller_id,
        s.seller_name,
        s.seller_type,
        COUNT(oi.item_id) as total_units_shipped,
        COUNT(r.return_id) as total_units_returned,
        SUM(CASE WHEN r.return_reason IN ('Defective', 'Damaged in Transit') THEN 1 ELSE 0 END) AS defective_returns,
        SUM(r.refund_amount + r.reverse_logistics_cost) AS direct_seller_leakage
    FROM sellers s
    JOIN products p ON s.seller_id = p.seller_id
    JOIN order_items oi ON p.product_id = oi.product_id
    LEFT JOIN returns r ON oi.item_id = r.item_id
    GROUP BY s.seller_id, s.seller_name, s.seller_type
),
RankedSellers AS (
    SELECT 
        seller_id,
        seller_name,
        seller_type,
        total_units_shipped,
        total_units_returned,
        defective_returns,
        ROUND((defective_returns::NUMERIC / NULLIF(total_units_shipped, 0)) * 100, 2) AS defect_rate_pct,
        direct_seller_leakage,
        DENSE_RANK() OVER (ORDER BY direct_seller_leakage DESC NULLS LAST) AS leakage_rank,
        SUM(direct_seller_leakage) OVER (ORDER BY direct_seller_leakage DESC NULLS LAST) AS running_leakage_total,
        SUM(direct_seller_leakage) OVER () AS global_seller_leakage
    FROM SellerMetrics
)
SELECT 
    seller_id,
    seller_name,
    seller_type,
    total_units_shipped,
    defective_returns,
    defect_rate_pct,
    direct_seller_leakage,
    leakage_rank,
    ROUND((running_leakage_total / global_seller_leakage) * 100, 2) AS pareto_cumulative_leakage_pct
FROM RankedSellers
WHERE leakage_rank <= 20
ORDER BY leakage_rank ASC;

-- ============================================================================
-- QUERY 3: Regional Leakage Cohort & Root Cause Matrix
-- ============================================================================
SELECT 
    c.region,
    r.return_reason,
    COUNT(r.return_id) AS total_return_events,
    SUM(r.refund_amount) AS aggregate_refunded,
    ROUND(AVG(r.reverse_logistics_cost), 2) AS avg_unit_reverse_cost,
    RANK() OVER (PARTITION BY c.region ORDER BY COUNT(r.return_id) DESC) AS regional_reason_rank
FROM returns r
JOIN order_items oi ON r.item_id = oi.item_id
JOIN orders o ON oi.order_id = o.order_id
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY c.region, r.return_reason;