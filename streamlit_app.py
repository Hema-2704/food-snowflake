import streamlit as st
import pandas as pd
import altair as alt
import snowflake.connector

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="Food Delivery Dashboard",
    layout="wide",
    page_icon="🍔"
)

st.title("🍔 Food Delivery Analytics Dashboard")
st.markdown("### 🚀 Streamlit Cloud + Snowflake Dashboard")

# -----------------------------
# LOAD DATA FROM SNOWFLAKE
# -----------------------------
@st.cache_data
def load_data():
    try:
        conn = snowflake.connector.connect(
            user=st.secrets["snowflake"]["user"],
            password=st.secrets["snowflake"]["password"],
            account=st.secrets["snowflake"]["account"],
            warehouse=st.secrets["snowflake"]["warehouse"],
            database=st.secrets["snowflake"]["database"],
            schema=st.secrets["snowflake"]["schema"]
        )

        query = """
            SELECT 
                ORDER_ID,
                USER_ID,
                RESTAURANT_ID,
                AMOUNT,
                CITY,
                ORDER_DATE
            FROM LOAD_D.RAW.ORDERS
        """

        df = pd.read_sql(query, conn)
        conn.close()

        # Date processing
        df['ORDER_DATE'] = pd.to_datetime(df['ORDER_DATE'])
        df['Year'] = df['ORDER_DATE'].dt.year
        df['Month'] = df['ORDER_DATE'].dt.month

        return df

    except Exception as e:
        st.error(f"❌ Snowflake Connection Error: {e}")
        st.stop()

df = load_data()

# -----------------------------
# DATA VALIDATION
# -----------------------------
st.sidebar.markdown("## ⚠️ Data Quality")

nulls = df.isnull().sum().sum()
negative = (df['AMOUNT'] < 0).sum()

if nulls > 0:
    st.sidebar.warning(f"NULL values: {nulls}")
else:
    st.sidebar.success("No NULL values")

if negative > 0:
    st.sidebar.error("Negative revenue found")
else:
    st.sidebar.success("Revenue valid")

# -----------------------------
# FILTERS
# -----------------------------
st.sidebar.markdown("## 🔎 Filters")

year_filter = st.sidebar.multiselect(
    "Year",
    sorted(df['Year'].unique()),
    default=sorted(df['Year'].unique())
)

month_filter = st.sidebar.multiselect(
    "Month",
    sorted(df['Month'].unique()),
    default=sorted(df['Month'].unique())
)

city_filter = st.sidebar.multiselect(
    "City",
    sorted(df['CITY'].unique()),
    default=sorted(df['CITY'].unique())
)

filtered_df = df[
    (df['Year'].isin(year_filter)) &
    (df['Month'].isin(month_filter)) &
    (df['CITY'].isin(city_filter))
]

# -----------------------------
# KPI METRICS
# -----------------------------
total_orders = len(filtered_df)
total_revenue = filtered_df['AMOUNT'].sum()
avg_order = filtered_df['AMOUNT'].mean()
users = filtered_df['USER_ID'].nunique()

# Growth calculation
prev_revenue = df['AMOUNT'].sum()
growth = ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue != 0 else 0

st.markdown("## 📊 Key Metrics")

col1, col2, col3, col4 = st.columns(4)

col1.metric("📦 Orders", total_orders)
col2.metric("💰 Revenue", f"₹{total_revenue:,.0f}", f"{growth:.1f}%")
col3.metric("📊 Avg Order", f"₹{avg_order:.2f}")
col4.metric("👤 Users", users)

st.markdown("---")

# -----------------------------
# VALIDATION
# -----------------------------
st.subheader("🔍 Validation")

sf_total_revenue = df['AMOUNT'].sum()
sf_orders = len(df)

colv1, colv2 = st.columns(2)

with colv1:
    if abs(sf_total_revenue - total_revenue) < 1:
        st.success("✅ Revenue Validated")
    else:
        st.error("❌ Revenue Mismatch")

with colv2:
    if sf_orders == total_orders:
        st.success("✅ Orders Validated")
    else:
        st.warning("⚠️ Orders Mismatch")

st.markdown("---")

# -----------------------------
# CHARTS
# -----------------------------
st.markdown("## 📈 Insights")

colA, colB = st.columns(2)

# Revenue Trend
trend = filtered_df.groupby('ORDER_DATE')['AMOUNT'].sum().reset_index()

chart1 = alt.Chart(trend).mark_line(point=True).encode(
    x='ORDER_DATE:T',
    y='AMOUNT:Q',
    tooltip=['ORDER_DATE', 'AMOUNT']
).properties(title="Revenue Trend")

colA.altair_chart(chart1, use_container_width=True)

# City Revenue
city_rev = filtered_df.groupby('CITY')['AMOUNT'].sum().reset_index()

chart2 = alt.Chart(city_rev).mark_bar().encode(
    x='CITY:N',
    y='AMOUNT:Q',
    color='AMOUNT:Q',
    tooltip=['CITY', 'AMOUNT']
).properties(title="Revenue by City")

colB.altair_chart(chart2, use_container_width=True)

# -----------------------------
# SECOND ROW
# -----------------------------
colC, colD = st.columns(2)

# Restaurant Orders
rest_orders = filtered_df['RESTAURANT_ID'].value_counts().reset_index()
rest_orders.columns = ['RESTAURANT_ID', 'ORDERS']

chart3 = alt.Chart(rest_orders).mark_bar().encode(
    x='RESTAURANT_ID:N',
    y='ORDERS:Q',
    tooltip=['RESTAURANT_ID', 'ORDERS']
).properties(title="Orders by Restaurant")

colC.altair_chart(chart3, use_container_width=True)

# Monthly Comparison
monthly = filtered_df.groupby(['Year', 'Month'])['AMOUNT'].sum().reset_index()

chart4 = alt.Chart(monthly).mark_bar().encode(
    x='Month:O',
    y='AMOUNT:Q',
    color='Year:N',
    tooltip=['Year', 'Month', 'AMOUNT']
).properties(title="Monthly Revenue Comparison")

colD.altair_chart(chart4, use_container_width=True)

# -----------------------------
# FOOTER
# -----------------------------
st.markdown("---")
st.caption("🚀 Streamlit Cloud + Snowflake | Production Dashboard")