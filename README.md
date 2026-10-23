# ReturnLeak AI — E-Commerce Return Loss Detection System

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-slatblue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.25+-red.svg)
![Pandas](https://img.shields.io/badge/Pandas-2.0+-green.svg)

An enterprise-level data analytics solution designed to isolate, quantify, and mitigate reverse-logistics financial leakage in modern multi-vendor e-commerce operations.

---

## 📌 Business Problem Definition
E-commerce reverse logistics often represents an invisible profit drain. Unmonitored return flows erode gross margins due to:
1. **Unchecked Reverse Shipping Costs**: Absorbing round-trip logistics expenses without vendor accountability.
2. **Category-Specific Sizing/Quality Mismatches**: High-volume return rates in Apparel and Footwear driven by poor sizing documentation.
3. **Vendor Defect Clustering**: A minority of third-party vendors shipping substandard goods, passing restocking and liquidation overhead back to the platform.

### Objectives
* Generate full relational datasets simulating **50,000+ realistic e-commerce transactions**.
* Run high-performance **PostgreSQL analytical queries** using window functions and CTEs to locate top cost drivers.
* Deliver an **Interactive Streamlit Dashboard** for business stakeholders to model mitigation strategies and track seller defect thresholds.
* Simulate targeted policy adjustments that **reduce net return loss by up to ~12%**.

---

## 🏗️ Technical Architecture & Stack
* **Language & Analysis**: Python 3.9+, Pandas, NumPy
* **Database & SQL Engine**: PostgreSQL (Compatible with ANSI SQL, Windowing functions, Recursive CTEs)
* **Visualization & Web App**: Streamlit, Plotly Express
* **Data Synthesis Engine**: Custom stochastic simulation (`generate_data.py`)

---

## 📊 Analytical Pipeline & Key Methodology

### 1. Data Generation & Ingestion Pipeline
The `generate_data.py` script creates six multi-relational schemas:
`sellers` ➔ `products` ➔ `customers` ➔ `orders` ➔ `order_items` ➔ `returns`

### 2. Advanced PostgreSQL Queries
Advanced analytical queries in `queries.sql` perform:
* **Category Leakage Breakdown**: Calculates gross margin vs. net shipping/scrapped losses.
* **Seller Pareto Analysis**: Uses `DENSE_RANK()` and running window totals (`SUM() OVER`) to rank seller risk profiles.
* **Regional Cohort Diagnostics**: Categorizes returns across geographical sectors to identify logistics bottlenecks.

### 3. Impact & Risk Quantification
Using Pareto analysis, the system isolates high-defect sellers (accounting for over proportional financial leakage) and sizing mismatches in apparel, modeling direct savings through offboarding and enhanced size guide deployment.

---

## 🛠️ Step-by-Step Installation & Execution Guide

### Prerequisites
* Python 3.9+ installed locally.
* Git installed.

### 1. Clone the Repository
```bash
git clone [https://github.com/prerna354/ReturnLeak-AI.git](https://github.com/your-username/ReturnLeak-AI.git)
cd ReturnLeak-AI
