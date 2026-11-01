
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Business Intelligence Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Business Intelligence Dashboard")
st.caption("Sales Performance | Customer Insights | Marketing Analytics")

# ==========================================
# 2. LOAD DATA
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data" / "processed"

@st.cache_data
def load_data():

    file_path = DATA_DIR / "thread_theory_cleaned.csv"

    data = pd.read_csv(file_path)

    data["Timestamp"] = pd.to_datetime(
        data["Timestamp"],
        errors="coerce"
    )

    data["Revenue"] = pd.to_numeric(
        data["Revenue"], errors="coerce"
    ).fillna(0)

    data["Ad Spend"] = pd.to_numeric(
        data["Ad Spend"], errors="coerce"
    ).fillna(0)

    data["Conversions"] = pd.to_numeric(
        data["Conversions"], errors="coerce"
    ).fillna(0)

    data = data.dropna(subset=["Timestamp"])

    data["Day_Type"] = np.where(
        data["Timestamp"].dt.dayofweek.isin([4, 5]),
        "Weekend",
        "Weekday"
    )

    data["Month_Period"] = (
        data["Timestamp"].dt.to_period("M").astype(str)
    )

    return data


try:
    df = load_data()

except Exception as e:
    st.error(f"Could not load dataset: {e}")
    st.stop()


# ==========================================
# 3. DATA SEPARATION
# ==========================================

sales_channels = ["Online", "In-Store"]

marketing_channels = [
    "Facebook",
    "Instagram",
    "Google Ads"
]

sales_df = df[
    df["Channel"].isin(sales_channels)
].copy()

marketing_df = df[
    df["Channel"].isin(marketing_channels)
].copy()


# ==========================================
# 4. SIDEBAR FILTERS
# ==========================================

st.sidebar.header("Dashboard Filters")

min_date = df["Timestamp"].min().date()
max_date = df["Timestamp"].max().date()

date_range = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if len(date_range) == 2:

    start_date, end_date = date_range

    if start_date > end_date:
        st.sidebar.error("Invalid date range.")
        st.stop()

else:
    start_date = date_range[0]
    end_date = date_range[0]


categories = sorted(df["Category"].dropna().unique())

selected_categories = st.sidebar.multiselect(
    "Product Category",
    categories,
    default=categories
)

customer_types = sorted(
    df["Customer Type"].dropna().unique()
)

selected_customers = st.sidebar.multiselect(
    "Customer Type",
    customer_types,
    default=customer_types
)

selected_day_type = st.sidebar.multiselect(
    "Day Type",
    ["Weekday", "Weekend"],
    default=["Weekday", "Weekend"]
)


# ==========================================
# 5. APPLY FILTERS
# ==========================================

def apply_filters(data):

    filtered = data[
        (data["Timestamp"].dt.date >= start_date) &
        (data["Timestamp"].dt.date <= end_date) &
        (data["Category"].isin(selected_categories)) &
        (data["Customer Type"].isin(selected_customers)) &
        (data["Day_Type"].isin(selected_day_type))
    ].copy()

    return filtered


filtered_sales = apply_filters(sales_df)

filtered_marketing = apply_filters(marketing_df)


# ==========================================
# 6. EXECUTIVE OVERVIEW
# ==========================================

st.header("Executive Overview")

total_revenue = filtered_sales["Revenue"].sum()

total_transactions = len(filtered_sales)

average_order_value = (
    total_revenue / total_transactions
    if total_transactions > 0 else 0
)

total_ad_spend = filtered_marketing["Ad Spend"].sum()

total_conversions = filtered_marketing["Conversions"].sum()

marketing_revenue = filtered_marketing["Revenue"].sum()

roas_proxy = (
    marketing_revenue / total_ad_spend
    if total_ad_spend > 0 else 0
)

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Sales Revenue",
    f"{total_revenue:,.2f}"
)

col2.metric(
    "Transactions",
    f"{total_transactions:,}"
)

col3.metric(
    "Average Order Value",
    f"{average_order_value:,.2f}"
)

col4.metric(
    "Marketing ROAS Proxy",
    f"{roas_proxy:.2f}x"
)

col5, col6, col7 = st.columns(3)

col5.metric(
    "Marketing Ad Spend",
    f"{total_ad_spend:,.2f}"
)

col6.metric(
    "Marketing Conversions",
    f"{total_conversions:,.0f}"
)

col7.metric(
    "Marketing Attributed Revenue",
    f"{marketing_revenue:,.2f}"
)

st.caption(
    "ROAS Proxy = Marketing-channel recorded revenue / Ad Spend. "
    "It is not verified incremental campaign ROAS."
)





# ==========================================
# 7. SALES PERFORMANCE
# ==========================================

st.divider()
st.header("Sales Performance")

col1, col2 = st.columns(2)

# Revenue by channel

channel_data = (
    filtered_sales.groupby("Channel")
    .agg(
        Revenue=("Revenue", "sum"),
        Transactions=("Revenue", "count")
    )
    .reset_index()
)

with col1:

    fig = px.bar(
        channel_data,
        x="Channel",
        y="Revenue",
        color="Channel",
        title="Revenue by Sales Channel",
        text_auto=".2s"
    )

    st.plotly_chart(fig, use_container_width=True)


# Monthly revenue

monthly_data = (
    filtered_sales.groupby("Month_Period")
    .agg(
        Revenue=("Revenue", "sum")
    )
    .reset_index()
)

with col2:

    fig = px.line(
        monthly_data,
        x="Month_Period",
        y="Revenue",
        markers=True,
        title="Monthly Sales Revenue"
    )

    st.plotly_chart(fig, use_container_width=True)


# ==========================================
# 8. CATEGORY ANALYSIS
# ==========================================

st.divider()
st.header("Product Category Analysis")

category_data = (
    filtered_sales.groupby("Category")
    .agg(
        Revenue=("Revenue", "sum"),
        Transactions=("Revenue", "count"),
        Average_Revenue=("Revenue", "mean")
    )
    .reset_index()
    .sort_values("Revenue", ascending=False)
)

col1, col2 = st.columns(2)

with col1:

    fig = px.bar(
        category_data,
        x="Category",
        y="Revenue",
        color="Category",
        title="Revenue by Category"
    )

    st.plotly_chart(fig, use_container_width=True)

with col2:

    fig = px.pie(
        category_data,
        names="Category",
        values="Revenue",
        hole=0.4,
        title="Category Revenue Contribution"
    )

    st.plotly_chart(fig, use_container_width=True)

st.dataframe(
    category_data.round(2),
    use_container_width=True,
    hide_index=True
)


# ==========================================
# 9. CUSTOMER ANALYSIS
# ==========================================

st.divider()
st.header("Customer Analysis")

customer_data = (
    filtered_sales.groupby("Customer Type")
    .agg(
        Revenue=("Revenue", "sum"),
        Transactions=("Revenue", "count"),
        Average_Revenue=("Revenue", "mean")
    )
    .reset_index()
)

col1, col2 = st.columns(2)

with col1:

    fig = px.bar(
        customer_data,
        x="Customer Type",
        y="Revenue",
        color="Customer Type",
        title="Revenue by Customer Type"
    )

    st.plotly_chart(fig, use_container_width=True)

with col2:

    fig = px.bar(
        customer_data,
        x="Customer Type",
        y="Average_Revenue",
        color="Customer Type",
        title="Average Revenue per Transaction"
    )

    st.plotly_chart(fig, use_container_width=True)


# ==========================================
# 10. WEEKEND VS WEEKDAY
# ==========================================

st.divider()
st.header("Weekend vs Weekday Analysis")

weekend_data = (
    filtered_sales.groupby("Day_Type")
    .agg(
        Revenue=("Revenue", "sum"),
        Transactions=("Revenue", "count"),
        Average_Revenue=("Revenue", "mean")
    )
    .reset_index()
)

col1, col2 = st.columns(2)

with col1:

    fig = px.bar(
        weekend_data,
        x="Day_Type",
        y="Revenue",
        color="Day_Type",
        title="Revenue: Weekend vs Weekday"
    )

    st.plotly_chart(fig, use_container_width=True)

with col2:

    fig = px.bar(
        weekend_data,
        x="Day_Type",
        y="Average_Revenue",
        color="Day_Type",
        title="Average Transaction Revenue"
    )

    st.plotly_chart(fig, use_container_width=True)


# ==========================================
# 11. MARKETING PERFORMANCE
# ==========================================

st.divider()
st.header("Marketing Performance")

marketing_summary = (
    filtered_marketing.groupby("Channel")
    .agg(
        Revenue=("Revenue", "sum"),
        Ad_Spend=("Ad Spend", "sum"),
        Conversions=("Conversions", "sum")
    )
    .reset_index()
)

marketing_summary["ROAS_Proxy"] = np.where(
    marketing_summary["Ad_Spend"] > 0,
    marketing_summary["Revenue"] /
    marketing_summary["Ad_Spend"],
    np.nan
)

marketing_summary["Cost_Per_Conversion"] = np.where(
    marketing_summary["Conversions"] > 0,
    marketing_summary["Ad_Spend"] /
    marketing_summary["Conversions"],
    np.nan
)

col1, col2 = st.columns(2)

with col1:

    fig = px.bar(
        marketing_summary,
        x="Channel",
        y="ROAS_Proxy",
        color="Channel",
        title="Marketing ROAS Proxy"
    )

    st.plotly_chart(fig, use_container_width=True)

with col2:

    fig = px.bar(
        marketing_summary,
        x="Channel",
        y="Ad_Spend",
        color="Channel",
        title="Advertising Spend by Channel"
    )

    st.plotly_chart(fig, use_container_width=True)

st.subheader("Marketing Performance Details")

st.dataframe(
    marketing_summary.round(2),
    use_container_width=True,
    hide_index=True
)


# ==========================================
# DYNAMIC BUSINESS RECOMMENDATIONS
# ==========================================

st.divider()
st.header("Dynamic Business Recommendations")

dynamic_recommendations = []

# 1. Sales Channel Analysis

if not filtered_sales.empty:

    channel_avg = (
        filtered_sales.groupby("Channel")["Revenue"].mean()
    )

    if "Online" in channel_avg.index and "In-Store" in channel_avg.index:

        online_avg = channel_avg["Online"]
        store_avg = channel_avg["In-Store"]

        if online_avg > store_avg:

            dynamic_recommendations.append({
                "Area": "Sales Channels",
                "Finding": "Online has higher average transaction revenue.",
                "Action": "Improve online checkout and product presentation.",
                "Priority": "High"
            })

        else:

            dynamic_recommendations.append({
                "Area": "Sales Channels",
                "Finding": "In-Store has higher average transaction revenue.",
                "Action": "Investigate in-store customer experience.",
                "Priority": "High"
            })


# 2. Weekend Performance

weekend_avg = (
    filtered_sales.groupby("Day_Type")["Revenue"].mean()
)

if "Weekend" in weekend_avg.index and "Weekday" in weekend_avg.index:

    if weekend_avg["Weekend"] < weekend_avg["Weekday"]:

        dynamic_recommendations.append({
            "Area": "Weekend Strategy",
            "Finding": "Weekend average transaction revenue is lower.",
            "Action": "Test targeted weekend promotions.",
            "Priority": "High"
        })


# 3. Customer Strategy

customer_avg = (
    filtered_sales.groupby("Customer Type")["Revenue"].mean()
)

if "Returning" in customer_avg.index and "New" in customer_avg.index:

    if customer_avg["Returning"] > customer_avg["New"]:

        dynamic_recommendations.append({
            "Area": "Customer Strategy",
            "Finding": "Returning customers generate higher average revenue.",
            "Action": "Test loyalty rewards and retention campaigns.",
            "Priority": "Medium"
        })


# 4. Marketing Performance

if not filtered_marketing.empty:

    ads = (
        filtered_marketing.groupby("Channel")
        .agg(
            Revenue=("Revenue", "sum"),
            Spend=("Ad Spend", "sum"),
            Conversions=("Conversions", "sum")
        )
    )

    ads = ads[ads["Spend"] > 0].copy()

    if not ads.empty:

        ads["ROAS_Proxy"] = ads["Revenue"] / ads["Spend"]

        best_channel = ads["ROAS_Proxy"].idxmax()

        dynamic_recommendations.append({
            "Area": "Marketing Strategy",
            "Finding": f"{best_channel} has the highest revenue-to-spend proxy.",
            "Action": f"Run a controlled performance test for {best_channel}.",
            "Priority": "Medium"
        })


# Display recommendations

if dynamic_recommendations:

    for rec in dynamic_recommendations:

        with st.expander(
            f"{rec['Area']} | {rec['Priority']}"
        ):

            st.write("**Finding:**", rec["Finding"])

            st.write("**Recommended Action:**", rec["Action"])

else:

    st.info("Insufficient data to generate recommendations for these filters.")



# ==========================================
# 13. DATA TABLE
# ==========================================

st.divider()
st.header("Filtered Sales Data")

st.dataframe(
    filtered_sales,
    use_container_width=True,
    hide_index=True
)

# ==========================================
# 14. FOOTER
# ==========================================

st.divider()

st.caption(
    "Business Intelligence & Analytics Project | "
    "Interactive Dashboard"
)




# ==========================================
# EXPORT CENTER
# ==========================================

st.divider()
st.header("Export Center")

col1, col2, col3 = st.columns(3)

with col1:

    csv_data = filtered_sales.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        label="Download Sales Data",
        data=csv_data,
        file_name="filtered_sales.csv",
        mime="text/csv"
    )

with col2:

    csv_data = marketing_summary.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        label="Download Marketing Report",
        data=csv_data,
        file_name="marketing_report.csv",
        mime="text/csv"
    )

with col3:

    if dynamic_recommendations:

        rec_df = pd.DataFrame(dynamic_recommendations)

        rec_csv = rec_df.to_csv(index=False).encode("utf-8-sig")

        st.download_button(
            label="Download Recommendations",
            data=rec_csv,
            file_name="business_recommendations.csv",
            mime="text/csv"
        )

    else:

        st.button(
            "No Recommendations Available",
            disabled=True
        )
