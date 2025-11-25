import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# =====================================================================
# BLOK FUNGSI UNTUK MENGHITUNG RFM
# =====================================================================
@st.cache_data
def create_seller_rfm_df(df):
    NOW = df['order_purchase_timestamp'].max() + pd.Timedelta(days=1)
    
    rfm_df = df.groupby('seller_id').agg(
        Recency_Days=('order_purchase_timestamp', lambda x: (NOW - x.max()).days),
        Frequency_Total_Orders=('order_id', 'nunique'),
        Monetary_Total_Revenue=('total_payment_value', 'sum')
    ).reset_index()

    rfm_df = rfm_df.rename(columns={
        'Recency_Days': 'Recency (Days Since Last Delivery)',
        'Frequency_Total_Orders': 'Frequency (Total Orders)',
        'Monetary_Total_Revenue': 'Monetary (Total Revenue Before Commission)'
    })
    
    return rfm_df


# =====================================================================
# BLOK PEMBACAAN DATA UTAMA
# =====================================================================
st.header('Olits E-Commerce Platform Dashboard :sparkles:')

GOOGLE_DRIVE_DOWNLOAD_URL = "https://drive.google.com/uc?export=download&id=1RqTC-Vgrjx3NvpDaGG07Dnwu9bz44XqV"

try:
    all_data_df = pd.read_csv(GOOGLE_DRIVE_DOWNLOAD_URL)
    st.success("Data berhasil dimuat dari Google Drive! 🚀")
except Exception as e:
    st.error(f"Gagal memuat data dari Google Drive. Error: {e}")
    st.stop()


# =====================================================================
# KONVERSI & PERSIAPAN DATA
# =====================================================================
if not pd.api.types.is_datetime64_any_dtype(all_data_df['order_purchase_timestamp']):
    all_data_df['order_purchase_timestamp'] = pd.to_datetime(all_data_df['order_purchase_timestamp'])


# =====================================================================
# 🔍 SIDEBAR FILTERS: tanggal dan state
# =====================================================================
st.sidebar.header("📅 Filter Data")

# Filter tanggal
min_date = all_data_df['order_purchase_timestamp'].min()
max_date = all_data_df['order_purchase_timestamp'].max()
start_date, end_date = st.sidebar.date_input(
    "Rentang Tanggal Order:",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# Filter berdasarkan STATE
state_column = None
if 'customer_state' in all_data_df.columns:
    state_column = 'customer_state'
elif 'seller_state' in all_data_df.columns:
    state_column = 'seller_state'

selected_states = None
if state_column:
    unique_states = all_data_df[state_column].dropna().unique()
    selected_states = st.sidebar.multiselect(
        "Pilih State:",
        options=sorted(unique_states),
        default=sorted(unique_states)
    )

# Terapkan filter ke dataset utama
filtered_df = all_data_df[
    (all_data_df['order_purchase_timestamp'].dt.date >= start_date) &
    (all_data_df['order_purchase_timestamp'].dt.date <= end_date)
]
if state_column and selected_states:
    filtered_df = filtered_df[filtered_df[state_column].isin(selected_states)]

st.sidebar.write(f"📊 Total data terfilter: {len(filtered_df):,} baris")


# =====================================================================
# 📊 SCORECARD UTAMA (TOTAL REVENUE & TOTAL UNIQUE ORDERS)
# =====================================================================
total_revenue = filtered_df['total_payment_value'].sum()
total_unique_orders = filtered_df['order_id'].nunique()

# Layout 2 kolom untuk scorecard
col1, col2 = st.columns(2)

with col1:
    st.metric(
        label="💰 Total Revenue",
        value=f"Rp {total_revenue:,.0f}",
        help="Total pendapatan berdasarkan filter aktif"
    )

with col2:
    st.metric(
        label="📦 Total Unique Orders",
        value=f"{total_unique_orders:,}",
        help="Jumlah order unik berdasarkan filter aktif"
    )

st.markdown("---")  # Garis pemisah visual


# =====================================================================
# PEMBUATAN VISUALISASI
# =====================================================================
filtered_df['order_month_year'] = filtered_df['order_purchase_timestamp'].dt.to_period('M')

# Agregasi performa bulanan
monthly_performance_df = filtered_df.groupby('order_month_year').agg(
    total_orders=('order_id', 'nunique'),
    total_revenue=('total_payment_value', 'sum')
).reset_index()

monthly_performance_df['order_month_year'] = monthly_performance_df['order_month_year'].astype(str)


# =====================================================================
# 1. Performa Penjualan dan Revenue Platform 📈
# =====================================================================
fig1, ax1 = plt.subplots(figsize=(15, 7))
sns.lineplot(
    x='order_month_year', y='total_revenue',
    data=monthly_performance_df, marker='o',
    linewidth=2, color="#72BCD4", ax=ax1
)
ax1.set_title("Total Revenue per Month", loc="center", fontsize=20)
ax1.set_xlabel("Month and Year", fontsize=12)
ax1.set_ylabel("Total Revenue", fontsize=12)
ax1.tick_params(axis='x', labelsize=10)
plt.setp(ax1.get_xticklabels(), rotation=45, ha='right')
ax1.tick_params(axis='y', labelsize=10)
ax1.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
st.pyplot(fig1)


# =====================================================================
# 2. Produk dan Kategori Paling/Paling Sedikit Diminati 🛍️
# =====================================================================
product_counts = filtered_df['product_id'].value_counts()
most_popular_products = product_counts.head(10)
least_popular_products = product_counts.tail(10)
category_counts = filtered_df['product_category_name_english'].value_counts()

fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(20, 15))
plot_color = "#72BCD4"

sns.barplot(x=most_popular_products.values, y=most_popular_products.index, color=plot_color, ax=axes[0, 0])
axes[0, 0].set_xlabel("Number of Orders")
axes[0, 0].set_title("Top 10 Most Popular Products", fontsize=15)
axes[0, 0].tick_params(axis='y', labelsize=10)

sns.barplot(x=least_popular_products.values, y=least_popular_products.index, color=plot_color, ax=axes[0, 1])
axes[0, 1].invert_xaxis()
axes[0, 1].yaxis.tick_right()
axes[0, 1].set_xlabel("Number of Orders")
axes[0, 1].set_title("Bottom 10 Least Popular Products", fontsize=15)
axes[0, 1].tick_params(axis='y', labelsize=10)

sns.barplot(x=category_counts.head(10).values, y=category_counts.head(10).index, color=plot_color, ax=axes[1, 0])
axes[1, 0].set_xlabel("Number of Orders")
axes[1, 0].set_title("Top 10 Most Popular Product Categories", fontsize=15)
axes[1, 0].tick_params(axis='y', labelsize=10)

sns.barplot(x=category_counts.tail(10).values, y=category_counts.tail(10).index, color=plot_color, ax=axes[1, 1])
axes[1, 1].invert_xaxis()
axes[1, 1].yaxis.tick_right()
axes[1, 1].set_xlabel("Number of Orders")
axes[1, 1].set_title("Bottom 10 Least Popular Product Categories", fontsize=15)
axes[1, 1].tick_params(axis='y', labelsize=10)

plt.suptitle("Product and Category Popularity Overview", fontsize=20, y=1.02)
plt.tight_layout(rect=[0, 0, 1, 0.98])
st.pyplot(fig)


# =====================================================================
# 3, 4, dan 5. Analisis Kinerja Seller (RFM) 🥇
# =====================================================================
seller_rfm_df = create_seller_rfm_df(filtered_df)

def plot_rfm_metric_chart(df, metric_col, title, ylabel, ascending_order=False, top_n=5, plot_color="#72BCD4"):
    sorted_df = df.sort_values(by=metric_col, ascending=ascending_order).head(top_n)
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(y=metric_col, x="seller_id", data=sorted_df, color=plot_color, ax=ax)
    ax.set_title(title, fontsize=18)
    ax.set_xlabel("Seller ID", fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right', fontsize=10)
    plt.yticks(fontsize=10)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    st.pyplot(fig)

st.subheader("Top 5 Seller berdasarkan Recency")
plot_rfm_metric_chart(
    seller_rfm_df,
    metric_col='Recency (Days Since Last Delivery)',
    title='Top 5 Sellers by Recency (Days Since Last Delivery)',
    ylabel='Recency (Days)',
    ascending_order=True
)

st.subheader("Top 5 Seller berdasarkan Frequency")
plot_rfm_metric_chart(
    seller_rfm_df,
    metric_col='Frequency (Total Orders)',
    title='Top 5 Sellers by Frequency (Total Orders)',
    ylabel='Frequency (Total Orders)',
    ascending_order=False
)

st.subheader("Top 5 Seller berdasarkan Monetary")
plot_rfm_metric_chart(
    seller_rfm_df,
    metric_col='Monetary (Total Revenue Before Commission)',
    title='Top 5 Sellers by Monetary (Total Revenue Before Commission)',
    ylabel='Monetary (Total Revenue Before Commission)',
    ascending_order=False
)
