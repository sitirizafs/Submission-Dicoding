#import seluruh library
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency
import pipreqs
sns.set(style='dark') 


##siapkan helper function
#membuat dataframe baru create_daily_order_df() untuk menyiapkan daily_orders_df
def create_daily_orders_df(df):
    daily_orders_df = df.resample(rule='D', on='order_purchase_timestamp').agg({
        "order_id": "nunique",
        "price": "sum"
    })
    daily_orders_df = daily_orders_df.reset_index()
    daily_orders_df.rename(columns={
        "order_id": "order_count",
        "price": "revenue"
    }, inplace=True)
    
    return daily_orders_df

#membuat dataframe baru create_sum_orders_items_df() untuk menyiapkan sum_orders_items_df
def create_sum_order_items_df(df):
    sum_order_items_df = df.groupby("product_category_name").quantity.sum().sort_values(ascending=False).reset_index()
    return sum_order_items_df

#membuat dataframe baru create_by_city_df() untuk menyiapkan by_city_df
def create_by_city_df(df):
    by_city_df = df.groupby(by="seller_city").seller_id.nunique().reset_index()
    by_city_df.rename(columns={
        "seller_id": "seller_count"
    }, inplace=True)
    
    return by_city_df

#membuat dataframe baru create_by_state_df() untuk menyiapkan by_state_df
def create_by_state_df(df):
    by_state_df = df.groupby(by="seller_state").seller_id.nunique().reset_index()
    by_state_df.rename(columns={
        "seller_id": "seller_count"
    }, inplace=True)
    
    return by_state_df

#membuat dataframe baru create_rfm_df() untuk menyiapkan rfm_df
def create_rfm_df(df):
    rfm_df = df.groupby(by="customer_id", as_index=False).agg({
        "order_purchase_timestamp": "max",
        "order_id": "nunique",
        "price": "sum"
    })
    rfm_df.columns = ["customer_id", "max_order_timestamp", "frequency", "monetary"]

#memperpendek customer_id menjadi inisial (4 karakter di depan)
    rfm_df["customer_id_initial"] = rfm_df["customer_id"].str[:4]

    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date
    recent_date = df["order_purchase_timestamp"].dt.date.max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)
    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)
    
    return rfm_df

##load berkas 'all_data.csv'
all_info_product_df = pd.read_csv("dashboard/all_data.csv")

#mengurutkan dataframe kolom
datetime_columns = ["order_purchase_timestamp", "order_delivered_carrier_date"]
all_info_product_df.sort_values(by="order_purchase_timestamp", inplace=True)
all_info_product_df.reset_index(inplace=True)
 
for column in datetime_columns:
    all_info_product_df[column] = pd.to_datetime(all_info_product_df[column])

##Membuat komponen filter
#membuat filter dengan widget date input dan menambahkan logo perusahaan pada sidebar
min_date = all_info_product_df["order_purchase_timestamp"].min()
max_date = all_info_product_df["order_purchase_timestamp"].max()
 
with st.sidebar:
    # Mengambil start_date & end_date dari date_input
    start_date = st.date_input(
        label='Tanggal Mulai',
        min_value=min_date,
        max_value=max_date,
        value=min_date
    )
    
    end_date = st.date_input(
        label='Tanggal Selesai',
        min_value=min_date,
        max_value=max_date,
        value=max_date
    )

# Memfilter start_date & end_date untuk all_info_product_df
main_df = all_info_product_df[(all_info_product_df["order_purchase_timestamp"] >= pd.Timestamp(start_date)) & 
                               (all_info_product_df["order_purchase_timestamp"] <= pd.Timestamp(end_date))]

#main_df ini akan menghasilkan dataframe yang telah dibuat sebelumnya
daily_orders_df = create_daily_orders_df(main_df)
sum_order_items_df = create_sum_order_items_df(main_df)
by_city_df = create_by_city_df(main_df)
by_state_df = create_by_state_df(main_df)
rfm_df = create_rfm_df(main_df)

##Melengkapi dashboard dengan berbagai visualisasi data
#menambahkan header pada dashboard
st.header('Brazilian Ecommerce Dashboard')

#menampilkan informasi total order dan revenue
st.subheader('Daily Orders')
 
col1, col2 = st.columns(2)
 
with col1:
    total_orders = daily_orders_df.order_count.sum()
    st.metric("Total orders", value=total_orders)
 
with col2:
    total_revenue = format_currency(daily_orders_df.revenue.sum(), "AUD", locale='es_CO') 
    st.metric("Total Revenue", value=total_revenue)
 
fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(
    daily_orders_df["order_purchase_timestamp"],
    daily_orders_df["order_count"],
    marker='o', 
    linewidth=2,
    color="#90CAF9"
)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)
 
st.pyplot(fig)

#menampilkan performa penjualan produk
st.subheader("Best & Worst Performing Product Best & Worst Performing Products in Last 3 Months")
fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(24, 6))

# Best Performing Products
# Filter data untuk 3 bulan terakhir di tahun 2018
filtered_data = all_info_product_df[
    (all_info_product_df['order_purchase_timestamp'] >= '2018-06-01') &
    (all_info_product_df['order_purchase_timestamp'] <= '2018-08-31')
]

# Mendapatkan 5 produk terlaris berdasarkan quantity
top_5_best = all_info_product_df[['product_category_name', 'quantity']].head(5)

# Mendapatkan 5 produk terendah berdasarkan quantity
top_5_worst = all_info_product_df.sort_values(by="quantity", ascending=True).head(5)

# Membuat visualisasi
fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(24, 6))

colors = ["#72BCD4", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
sns.barplot(
    x="quantity",
    y="product_category_name",
    data=top_5_best,
    palette=colors,
    ax=ax[0]
)
ax[0].set_ylabel('Product Category', fontsize=30)
ax[0].set_xlabel('Total Sales', fontsize=30)
ax[0].set_title("Top 5 Best Performing Products (June - August 2018)", loc="right", fontsize=26)
ax[0].tick_params(axis='y', labelsize=20)
ax[0].tick_params(axis='x', labelsize=20)
 
 # Worst Performing Products
sns.barplot(
    x="quantity",
    y="product_category_name",
    data=top_5_worst,
    palette=colors,
    ax=ax[1]
)
ax[1].set_ylabel('Product Category', fontsize=30)
ax[1].set_xlabel('Total Sales', fontsize=30)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Top 5 Worst Performing Products (June - August 2018)", loc="right", fontsize=26)
ax[1].tick_params(axis='y', labelsize=20)
ax[1].tick_params(axis='x', labelsize=20)
 
st.pyplot(fig)

#menampilkan demografi seller
st.subheader("Seller Demographics")
 
col1, col2 = st.columns(2)
 
with col1:
    fig, ax = plt.subplots(figsize=(20, 10))
 
    sns.barplot(
        y="seller_count", 
        x="seller_city",
        data=by_city_df.sort_values(by="seller_count", ascending=False).head(5),
        palette=colors,
        ax=ax
    )
    ax.set_title("Number of Seller by City", loc="center", fontsize=50)
    ax.set_ylabel(None)
    ax.set_xlabel(None)
    ax.tick_params(axis='x', labelsize=35)
    ax.tick_params(axis='y', labelsize=30)
    st.pyplot(fig)
 
with col2:
    fig, ax = plt.subplots(figsize=(20, 10))
    
    colors = ["#D3D3D3", "#90CAF9", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
 
    sns.barplot(
        y="seller_count", 
        x="seller_state",
        data=by_state_df.sort_values(by="seller_state", ascending=False).head(5),
        palette=colors,
        ax=ax
    )
    ax.set_title("Number of Customer by State", loc="center", fontsize=50)
    ax.set_ylabel(None)
    ax.set_xlabel(None)
    ax.tick_params(axis='x', labelsize=35)
    ax.tick_params(axis='y', labelsize=30)
    st.pyplot(fig)
 
#menampilkan parameter RFM
st.subheader("Top 5 Best Customers based on Recency, Frequency, and Monetary")
 
col1, col2, col3 = st.columns(3)
 
with col1:
    avg_recency = round(rfm_df.recency.mean(), 1)
    st.metric("Average Recency (days)", value=avg_recency)
 
with col2:
    avg_frequency = round(rfm_df.frequency.mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)
 
with col3:
    avg_frequency = format_currency(rfm_df.monetary.mean(), "AUD", locale='es_CO') 
    st.metric("Average Monetary", value=avg_frequency)
 
fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(35, 15))
colors = ["#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9"]
 
# Plot Recency
sns.histplot(rfm_df['recency'], kde=True, ax=ax[0], color="#72BCD4")
ax[0].set_xlabel("Recency (Days)", fontsize=15)
ax[0].set_ylabel("Frequency", fontsize=15)
ax[0].set_title("Distribution of Recency (Days)", loc="center", fontsize=40)
ax[0].tick_params(axis='y', labelsize=30)
ax[0].tick_params(axis='x', labelsize=35)

# Plot Frequency
sns.histplot(rfm_df['frequency'], kde=True, ax=ax[1], color="#72BCD4")
ax[1].set_xlabel("Customer ID", fontsize=15)
ax[1].set_ylabel("Frequency", fontsize=15)
ax[1].set_title("Top Customers by Frequency", loc="center", fontsize=40)
ax[1].tick_params(axis='y', labelsize=30)
ax[1].tick_params(axis='x', labelsize=35)
 
# Plot Monetary
sns.histplot(rfm_df['monetary'], kde=True, ax=ax[2], color="#72BCD4")
ax[2].set_xlabel("Monetary Value", fontsize=15)
ax[2].set_ylabel("Frequency", fontsize=15)
ax[2].set_title("Distribution of Monetary", loc="center", fontsize=40)
ax[2].tick_params(axis='y', labelsize=30)
ax[2].tick_params(axis='x', labelsize=35)
 
st.pyplot(fig)
 
st.caption('Copyright (c) Brazilian ecommerce 2024')
