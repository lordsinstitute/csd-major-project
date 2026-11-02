import streamlit as st
import pandas as pd
import psycopg2
def get_db_connection():
    conn = psycopg2.connect(
        host=st.secrets["postgres"]["host"],
        port=st.secrets["postgres"]["port"],
        dbname=st.secrets["postgres"]["database"],
        user=st.secrets["postgres"]["user"],
        password=st.secrets["postgres"]["password"]
    )
    return conn
# Sidebar navigation
st.sidebar.title("Navigation")
st.sidebar.caption("Product Demand & Inventory")

page = st.sidebar.selectbox(
    "Choose a section",
    ["Overview", "Upload Data", "Demand Forecast", "Inventory Optimization", "Business Dashboard"]
)

# Main application title
st.title("Product Demand Forecasting & Inventory Optimization")

# Overview section
if page == "Overview":
    st.subheader("Project Overview")

    st.write(
        "An interactive analytics platform for forecasting product demand "
        "and optimizing inventory decisions using historical sales data."
    )

    st.subheader("Key Features")

    st.markdown("""
    - Upload and analyze historical sales data
    - Forecast future product demand
    - Calculate recommended inventory levels
    - Identify products that may need restocking
    - View results through interactive charts
    """)

    st.divider()
    st.success("Application is running successfully!")
    st.info("Welcome to the project overview.")

# Upload Data section
elif page == "Upload Data":
    st.subheader("Upload Sales Data")

    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=["csv"]
    )

    if uploaded_file is not None:
        st.success(f"File selected: {uploaded_file.name}")

        df = pd.read_csv(uploaded_file)
        
        
        if st.button("Save uploaded data to PostgreSQL"):
            required_columns = [
                "date",
                "product_id",
                "product_name",
                "units_sold",
                "stock_on_hand",
                "lead_time_days"
            ]

            missing_columns = [
                col for col in required_columns
                if col not in df.columns
            ]

            if missing_columns:
                st.error(
                    f"Missing required columns: {missing_columns}"
                )
            elif df.empty:
                st.error("The uploaded CSV contains no data.")
            
            else:
                try:
                    save_df = df[required_columns].copy()

                    save_df["date"] = pd.to_datetime(
                        save_df["date"], errors="raise"
                    ).dt.date

                    for col in [
                        "units_sold",
                        "stock_on_hand",
                        "lead_time_days"
                    ]:
                        save_df[col] = pd.to_numeric(
                            save_df[col], errors="raise"
                        )

                    if save_df.isnull().any().any():
                        st.error("The CSV contains missing required values.")
                    elif (
                        save_df[
                            ["units_sold", "stock_on_hand", "lead_time_days"]
                        ] < 0
                    ).any().any():
                        st.error("Inventory and sales values cannot be negative.")
                    else:
                        conn = get_db_connection()
                        cursor = conn.cursor()

                        insert_query = """
                            INSERT INTO sales_data
                            (date, product_id, product_name, units_sold,
                             stock_on_hand, lead_time_days)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """

                        rows = list(
                            save_df.itertuples(index=False, name=None)
                        )
                        cursor.executemany(insert_query, rows)
                        conn.commit()

                        cursor.close()
                        conn.close()

                        st.success(
                            f"Successfully saved {len(rows)} rows to PostgreSQL!"
                        )

                except Exception as e:
                    st.error(f"Could not save data: {e}")



        # Dataset dimensions
        st.write("Number of rows:", df.shape[0])
        st.write("Number of columns:", df.shape[1])

        # Date range
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            valid_dates = df["date"].dropna()

            if not valid_dates.empty:
                st.write("Earliest Date:", valid_dates.min().date())
                st.write("Latest Date:", valid_dates.max().date())
            else:
                st.warning("The date column does not contain valid dates.")
        else:
            st.warning("The dataset does not contain a date column.")

        # Total units sold
        if "units_sold" in df.columns:
            total_units_sold = df["units_sold"].sum()
            st.metric("Total Units Sold", total_units_sold)
        else:
            st.warning("The dataset does not contain a units_sold column.")

        # Latest stock on hand for each product
        if all(
            column in df.columns
            for column in ["date", "product_id", "stock_on_hand"]
        ):
            stock_data = df.dropna(
                subset=["date", "product_id", "stock_on_hand"]
            )

            latest_stock = (
                stock_data.sort_values("date")
                .groupby("product_id")
                .tail(1)
            )

            total_stock = latest_stock["stock_on_hand"].sum()

            st.metric("Latest Total Stock", total_stock)
            st.write("Latest stock for each product:")

            st.dataframe(
                latest_stock[["product_id", "stock_on_hand"]],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning(
                "Stock calculation requires date, product_id, "
                "and stock_on_hand columns."
            )

        # Unique products
        if "product_id" in df.columns:
            st.write(
                "Number of unique products:",
                df["product_id"].nunique()
            )
        else:
            st.warning("The dataset does not contain a product_id column.")

        # Duplicate rows check
        st.subheader("Duplicate Rows")

        duplicate_count = df.duplicated().sum()
        st.write("Number of duplicate rows:", duplicate_count)

        if duplicate_count == 0:
            st.success("Data quality check passed: No duplicate rows found.")
        else:
            st.warning("Duplicate rows detected. Review them before analysis.")

        # Missing values check
        st.subheader("Missing Values")

        st.dataframe(
            df.isnull().sum().reset_index(name="Missing Count")
        )

        if df.isnull().sum().sum() == 0:
            st.success("Data quality check passed: No missing values found.")
        else:
            st.warning("Missing values detected. Data cleaning may be required.")

        # Daily sales trend
        if "date" in df.columns and "units_sold" in df.columns:
            st.subheader("Daily Sales Trend")

            daily_sales = (
                df.dropna(subset=["date"])
                .groupby("date")["units_sold"]
                .sum()
                .sort_index()
            )

            st.line_chart(daily_sales)

        # Product selector and sales analysis
        if "product_id" in df.columns and "units_sold" in df.columns:
            products = sorted(df["product_id"].dropna().unique())

            if products:
                st.subheader("Sales Analysis")

                selected_product = st.selectbox(
                    "Choose a product",
                    products
                )

                product_df = df[df["product_id"] == selected_product]

                # Selected product's daily sales
                st.subheader(f"Daily Sales Trend: {selected_product}")

                if "date" in product_df.columns:
                    product_daily_sales = (
                        product_df.dropna(subset=["date"])
                        .groupby("date")["units_sold"]
                        .sum()
                        .sort_index()
                    )

                    st.line_chart(product_daily_sales)

                # Selected product summary
                st.subheader(f"Product Summary: {selected_product}")

                product_total = product_df["units_sold"].sum()
                st.metric("Total Units Sold", product_total)

                if (
                    "date" in product_df.columns
                    and "stock_on_hand" in product_df.columns
                ):
                    stock_records = product_df.dropna(
                        subset=["date", "stock_on_hand"]
                    )

                    if not stock_records.empty:
                        latest_product_stock = (
                            stock_records.sort_values("date")
                            .iloc[-1]["stock_on_hand"]
                        )

                        st.metric("Latest Stock", latest_product_stock)
                    else:
                        st.warning(
                            "No valid stock records found for this product."
                        )

                # Product-wise sales comparison
                st.subheader("Product-wise Sales Comparison")

                product_sales = (
                    df.groupby("product_id")["units_sold"]
                    .sum()
                    .sort_values(ascending=False)
                )

                st.bar_chart(product_sales)
            else:
                st.warning("No valid product IDs were found in the dataset.")

        # Data preview
        st.subheader("Data Preview")
        st.dataframe(df, use_container_width=True, hide_index=True)

elif page == "Demand Forecast":

    st.header("Demand Forecast")

    uploaded_file = st.file_uploader(
        "Upload your sales CSV file",
        type=["csv"],
        key="forecast_upload"
    )

    if uploaded_file is not None:

        df = pd.read_csv(uploaded_file)

        required_columns = [
            "date",
            "product_id",
            "units_sold"
        ]

        missing_columns = [
            col for col in required_columns
            if col not in df.columns
        ]

        if missing_columns:
            st.error(
                f"Missing columns: {missing_columns}"
            )

        else:

            df["date"] = pd.to_datetime(
                df["date"],
                errors="coerce"
            )

            df["units_sold"] = pd.to_numeric(
                df["units_sold"],
                errors="coerce"
            )

            df = df.dropna(
                subset=[
                    "date",
                    "product_id",
                    "units_sold"
                ]
            )

            products = sorted(
                df["product_id"].unique()
            )

            selected_product = st.selectbox(
                "Select Product",
                products,
                key="forecast_product"
            )

            product_data = df[
                df["product_id"] == selected_product
            ].copy()

            daily_demand = (
                product_data
                .groupby("date")["units_sold"]
                .sum()
                .sort_index()
            )

            if len(daily_demand) < 14:

                st.warning(
                    "At least 14 days of data are required "
                    "for demand forecasting."
                )

            else:

                test_days = 7

                train_data = daily_demand.iloc[
                    :-test_days
                ]

                test_data = daily_demand.iloc[
                    -test_days:
                ]

                # -----------------------------
                # MODEL 1: AVERAGE DEMAND
                # -----------------------------

                average_demand = train_data.mean()

                average_predictions = pd.Series(
                    [average_demand] * len(test_data),
                    index=test_data.index
                )

                average_mae = (
                    (test_data - average_predictions)
                    .abs()
                    .mean()
                )

                # -----------------------------
                # MODEL 2: 3-DAY MOVING AVERAGE
                # -----------------------------

                moving_average_predictions = []

                history = list(train_data.values)

                for actual_value in test_data.values:

                    previous_values = history[-3:]

                    prediction = sum(
                        previous_values
                    ) / len(previous_values)

                    moving_average_predictions.append(
                        prediction
                    )

                    history.append(actual_value)

                moving_average_predictions = pd.Series(
                    moving_average_predictions,
                    index=test_data.index
                )

                moving_average_mae = (
                    (
                        test_data
                        - moving_average_predictions
                    )
                    .abs()
                    .mean()
                )

                # -----------------------------
                # SELECT BETTER MODEL
                # -----------------------------

                if moving_average_mae < average_mae:

                    selected_model = "3-Day Moving Average"
                    selected_mae = moving_average_mae
                    forecast_demand = (
                        train_data.tail(3).mean()
                    )

                else:

                    selected_model = "Average Demand"
                    selected_mae = average_mae
                    forecast_demand = average_demand

                forecast_demand = round(
                    forecast_demand
                )

                seven_day_forecast = (
                    forecast_demand * 7
                )

                # -----------------------------
                # DISPLAY MODEL COMPARISON
                # -----------------------------

                st.subheader(
                    "Forecast Model Comparison"
                )

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "Average Method MAE",
                        round(average_mae, 2)
                    )

                with col2:
                    st.metric(
                        "Moving Average MAE",
                        round(
                            moving_average_mae,
                            2
                        )
                    )

                with col3:
                    st.metric(
                        "Selected Model",
                        selected_model
                    )
                    st.info(
                    f"Selected because it achieved the lower "
                    f"MAE of {selected_mae:.2f} units on the test data."
                )

                # -----------------------------
                # FORECAST SUMMARY
                # -----------------------------

                st.subheader(
                    "Forecast Summary"
                )

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "Average Daily Demand",
                        round(
                            average_demand,
                            2
                        )
                    )

                with col2:
                    st.metric(
                        "7-Day Forecast",
                        seven_day_forecast
                    )

                with col3:
                    st.metric(
                        "MAE",
                        round(
                            selected_mae,
                            2
                        )
                    )

                # -----------------------------
                # HISTORICAL DEMAND CHART
                # -----------------------------

                st.subheader(
                    "Historical Demand"
                )

                st.line_chart(
                    daily_demand
                )

                # -----------------------------
                # FORECAST VS ACTUAL
                # -----------------------------

                comparison_df = pd.DataFrame({
                    "Actual Demand": test_data,
                    "Average Method": average_predictions,
                    "3-Day Moving Average":
                        moving_average_predictions
                })

                st.subheader(
                    "Forecast vs Actual Demand"
                )

                st.line_chart(
                    comparison_df
                )

                # -----------------------------
                # FUTURE 7-DAY FORECAST
                # -----------------------------

                future_dates = pd.date_range(
                    start=daily_demand.index.max()
                    + pd.Timedelta(days=1),
                    periods=7
                )

                future_forecast = pd.Series(
                    [forecast_demand] * 7,
                    index=future_dates
                )

                st.subheader(
                    "Next 7 Days Demand Forecast"
                )

                st.line_chart(
                    future_forecast
                )

                # -----------------------------
                # FORECAST TABLE
                # -----------------------------

                forecast_table = (
                    future_forecast
                    .rename("Forecast Units")
                    .reset_index()
                )

                forecast_table = (
                    forecast_table.rename(
                        columns={
                            "index": "Forecast Date"
                        }
                    )
                )

                st.subheader(
                    "7-Day Forecast Table"
                )

                st.dataframe(
                    forecast_table,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Download Forecast Report
                st.subheader("📥 Download Forecast Report")

                forecast_csv = forecast_table.to_csv(
                    index=False
                ).encode("utf-8")

                st.download_button(
                    label="Download 7-Day Forecast (CSV)",
                    data=forecast_csv,
                    file_name="7_day_demand_forecast.csv",
                    mime="text/csv"
                )
elif page == "Inventory Optimization":

    st.header("Inventory Optimization")

    uploaded_file = st.file_uploader(
        "Upload your sales and inventory CSV file",
        type=["csv"],
        key="inventory_upload"
    )

    if uploaded_file is not None:

        df = pd.read_csv(uploaded_file)

        required_columns = [
            "date",
            "product_id",
            "product_name",
            "units_sold",
            "stock_on_hand",
            "lead_time_days"
        ]

        missing_columns = [
            col for col in required_columns
            if col not in df.columns
        ]

        if missing_columns:

            st.error(
                f"Missing columns: {missing_columns}"
            )

        else:

            df["date"] = pd.to_datetime(
                df["date"],
                errors="coerce"
            )

            df["units_sold"] = pd.to_numeric(
                df["units_sold"],
                errors="coerce"
            )

            df["stock_on_hand"] = pd.to_numeric(
                df["stock_on_hand"],
                errors="coerce"
            )

            df["lead_time_days"] = pd.to_numeric(
                df["lead_time_days"],
                errors="coerce"
            )

            df = df.dropna(
                subset=[
                    "date",
                    "product_id",
                    "product_name",
                    "units_sold",
                    "stock_on_hand",
                    "lead_time_days"
                ]
            )

            products = (
                df[
                    [
                        "product_id",
                        "product_name"
                    ]
                ]
                .drop_duplicates()
                .sort_values("product_id")
            )

            results = []

            for _, product in products.iterrows():

                product_id = product["product_id"]
                product_name = product["product_name"]

                product_data = df[
                    df["product_id"] == product_id
                ].copy()

                daily_demand = (
                    product_data
                    .groupby("date")["units_sold"]
                    .sum()
                    .sort_index()
                )

                latest_stock = (
                    product_data
                    .sort_values("date")
                    .iloc[-1]["stock_on_hand"]
                )

                lead_time = int(
                    product_data["lead_time_days"].iloc[-1]
                )

                # Need at least 14 days for forecasting
                if len(daily_demand) >= 14:

                    test_days = 7

                    train_data = daily_demand.iloc[
                        :-test_days
                    ]

                    test_data = daily_demand.iloc[
                        -test_days:
                    ]

                    # -----------------------------
                    # MODEL 1: AVERAGE DEMAND
                    # -----------------------------

                    average_demand = (
                        train_data.mean()
                    )

                    average_predictions = pd.Series(
                        [average_demand] * len(test_data),
                        index=test_data.index
                    )

                    average_mae = (
                        (
                            test_data
                            - average_predictions
                        )
                        .abs()
                        .mean()
                    )

                    # -----------------------------
                    # MODEL 2: 3-DAY MOVING AVERAGE
                    # -----------------------------

                    moving_average_predictions = []

                    history = list(
                        train_data.values
                    )

                    for actual_value in test_data.values:

                        previous_values = history[-3:]

                        prediction = (
                            sum(previous_values)
                            / len(previous_values)
                        )

                        moving_average_predictions.append(
                            prediction
                        )

                        history.append(
                            actual_value
                        )

                    moving_average_predictions = pd.Series(
                        moving_average_predictions,
                        index=test_data.index
                    )

                    moving_average_mae = (
                        (
                            test_data
                            - moving_average_predictions
                        )
                        .abs()
                        .mean()
                    )

                    # -----------------------------
                    # SELECT BEST MODEL
                    # -----------------------------

                    if moving_average_mae < average_mae:

                        selected_model = (
                            "3-Day Moving Average"
                        )

                        forecast_daily = (
                            train_data.tail(3).mean()
                        )

                    else:

                        selected_model = (
                            "Average Demand"
                        )

                        forecast_daily = (
                            average_demand
                        )

                    forecast_daily = round(
                        forecast_daily
                    )

                    # -----------------------------
                    # INVENTORY CALCULATIONS
                    # -----------------------------

                    seven_day_forecast = (
                        forecast_daily * 7
                    )

                    lead_time_demand = (
                        forecast_daily * lead_time
                    )

                    safety_stock = round(
                        lead_time_demand * 0.20
                    )

                    reorder_point = (
                        lead_time_demand
                        + safety_stock
                    )

                    recommended_order = max(
                        0,
                        seven_day_forecast
                        + safety_stock
                        - latest_stock
                    )

                    # -----------------------------
                    # INVENTORY STATUS
                    # -----------------------------

                    if latest_stock <= reorder_point:

                        status = "🔴 Reorder Now"

                    elif latest_stock <= (
                        reorder_point * 1.4
                    ):

                        status = "🟡 Monitor"

                    else:

                        status = "🟢 Stock Sufficient"

                    results.append({
                        "Product ID": product_id,
                        "Product Name": product_name,
                        "Current Stock": int(
                            latest_stock
                        ),
                        "Forecast Daily Demand": int(
                            forecast_daily
                        ),
                        "7-Day Forecast": int(
                            seven_day_forecast
                        ),
                        "Lead Time": lead_time,
                        "Lead-Time Demand": int(
                            lead_time_demand
                        ),
                        "Safety Stock": int(
                            safety_stock
                        ),
                        "Reorder Point": int(
                            reorder_point
                        ),
                        "Recommended Order": int(
                            recommended_order
                        ),
                        "Selected Model": selected_model,
                        "Status": status
                    })

                else:

                    st.warning(
                        f"{product_id} does not have "
                        "enough data for forecasting."
                    )

            # -----------------------------
            # RESULTS TABLE
            # -----------------------------

            if results:

                results_df = pd.DataFrame(
                    results
                )

                st.subheader(
                    "Forecast-Based Inventory Overview"
                )

                total_products = len(
                    results_df
                )

                reorder_count = (
                    results_df["Status"]
                    .eq("🔴 Reorder Now")
                    .sum()
                )

                monitor_count = (
                    results_df["Status"]
                    .eq("🟡 Monitor")
                    .sum()
                )

                sufficient_count = (
                    results_df["Status"]
                    .eq("🟢 Stock Sufficient")
                    .sum()
                )

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric(
                        "Total Products",
                        total_products
                    )

                with col2:
                    st.metric(
                        "Reorder Now",
                        reorder_count
                    )

                with col3:
                    st.metric(
                        "Monitor",
                        monitor_count
                    )

                with col4:
                    st.metric(
                        "Stock Sufficient",
                        sufficient_count
                    )

                st.subheader(
                    "Product-Wise Inventory Status"
                )

                display_columns = [
                    "Product ID",
                    "Product Name",
                    "Current Stock",
                    "Forecast Daily Demand",
                    "7-Day Forecast",
                    "Lead Time",
                    "Reorder Point",
                    "Recommended Order",
                    "Selected Model",
                    "Status"
                ]

                st.dataframe(
                    results_df[display_columns],
                    use_container_width=True,
                    hide_index=True
                )

                # -----------------------------
                # PRODUCT DETAIL
                # -----------------------------

                st.subheader(
                    "Detailed Product Analysis"
                )

                selected_product = st.selectbox(
                    "Select Product",
                    results_df["Product ID"].tolist(),
                    key="inventory_product"
                )

                selected_row = results_df[
                    results_df["Product ID"]
                    == selected_product
                ].iloc[0]

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric(
                        "Current Stock",
                        selected_row[
                            "Current Stock"
                        ]
                    )

                with col2:
                    st.metric(
                        "7-Day Forecast",
                        selected_row[
                            "7-Day Forecast"
                        ]
                    )

                with col3:
                    st.metric(
                        "Reorder Point",
                        selected_row[
                            "Reorder Point"
                        ]
                    )

                with col4:
                    st.metric(
                        "Recommended Order",
                        selected_row[
                            "Recommended Order"
                        ]
                    )

                st.subheader(
                    "Forecast-Based Reorder Analysis"
                )

                st.write(
                    "Selected forecasting model: "
                    f"**{selected_row['Selected Model']}**"
                )

                st.write(
                    "Forecasted demand for next 7 days: "
                    f"**{selected_row['7-Day Forecast']} units**"
                )

                st.write(
                    "Lead-time demand: "
                    f"**{selected_row['Lead-Time Demand']} units**"
                )

                st.write(
                    "Safety stock: "
                    f"**{selected_row['Safety Stock']} units**"
                )

                st.write(
                    "Reorder point: "
                    f"**{selected_row['Reorder Point']} units**"
                )

                st.write(
                    "Recommended order quantity: "
                    f"**{selected_row['Recommended Order']} units**"
                )

                st.write(
                    f"Inventory status: "
                    f"**{selected_row['Status']}**"
                )


elif page == "Business Dashboard":

    st.header("Business Dashboard")

    uploaded_file = st.file_uploader(
        "Upload your sales and inventory CSV file",
        type=["csv"],
        key="dashboard_upload"
    )

    if uploaded_file is not None:

        df = pd.read_csv(uploaded_file)

        st.success(
            f"File loaded successfully: {uploaded_file.name}"
        )

        # -----------------------------
        # BUSINESS KPI VARIABLES
        # -----------------------------

        total_products = df["product_id"].nunique()

        total_forecasted_demand = 0
        products_requiring_reorder = 0
        total_recommended_order = 0

        inventory_results = []

        products = df["product_id"].dropna().unique()

        for product_id in products:

            product_data = df[
                df["product_id"] == product_id
            ].copy()

            product_data["date"] = pd.to_datetime(
                product_data["date"],
                errors="coerce"
            )

            product_data["units_sold"] = pd.to_numeric(
                product_data["units_sold"],
                errors="coerce"
            )

            product_data["stock_on_hand"] = pd.to_numeric(
                product_data["stock_on_hand"],
                errors="coerce"
            )

            product_data["lead_time_days"] = pd.to_numeric(
                product_data["lead_time_days"],
                errors="coerce"
            )

            product_data = product_data.dropna(
                subset=[
                    "date",
                    "units_sold",
                    "stock_on_hand",
                    "lead_time_days"
                ]
            )

            daily_demand = (
                product_data
                .groupby("date")["units_sold"]
                .sum()
                .sort_index()
            )

            if len(daily_demand) >= 14:

                test_days = 7

                train_data = daily_demand.iloc[
                    :-test_days
                ]

                test_data = daily_demand.iloc[
                    -test_days:
                ]

                # -----------------------------
                # AVERAGE DEMAND MODEL
                # -----------------------------

                average_demand = train_data.mean()

                average_predictions = pd.Series(
                    [average_demand] * len(test_data),
                    index=test_data.index
                )

                average_mae = (
                    test_data - average_predictions
                ).abs().mean()

                # -----------------------------
                # 3-DAY MOVING AVERAGE MODEL
                # -----------------------------

                moving_average_predictions = []

                history = list(train_data.values)

                for actual_value in test_data.values:

                    previous_values = history[-3:]

                    prediction = (
                        sum(previous_values)
                        / len(previous_values)
                    )

                    moving_average_predictions.append(
                        prediction
                    )

                    history.append(actual_value)

                moving_average_predictions = pd.Series(
                    moving_average_predictions,
                    index=test_data.index
                )

                moving_average_mae = (
                    test_data
                    - moving_average_predictions
                ).abs().mean()

                # -----------------------------
                # SELECT BEST MODEL
                # -----------------------------

                if moving_average_mae < average_mae:

                    selected_model = (
                        "3-Day Moving Average"
                    )

                    forecast_daily = (
                        train_data.tail(3).mean()
                    )

                else:

                    selected_model = (
                        "Average Demand"
                    )

                    forecast_daily = average_demand

                forecast_daily = round(
                    forecast_daily
                )

                # -----------------------------
                # INVENTORY CALCULATIONS
                # -----------------------------

                latest_record = (
                    product_data
                    .sort_values("date")
                    .iloc[-1]
                )

                latest_stock = latest_record[
                    "stock_on_hand"
                ]

                lead_time = int(
                    latest_record[
                        "lead_time_days"
                    ]
                )

                seven_day_forecast = (
                    forecast_daily * 7
                )

                lead_time_demand = (
                    forecast_daily * lead_time
                )

                safety_stock = round(
                    lead_time_demand * 0.20
                )

                reorder_point = (
                    lead_time_demand
                    + safety_stock
                )

                recommended_order = max(
                    0,
                    seven_day_forecast
                    + safety_stock
                    - latest_stock
                )

                # -----------------------------
                # RISK STATUS
                # -----------------------------

                if latest_stock <= reorder_point:

                    status = "🔴 Reorder Now"

                    products_requiring_reorder += 1

                elif latest_stock <= (
                    reorder_point * 1.4
                ):

                    status = "🟡 Monitor"

                else:

                    status = "🟢 Stock Sufficient"

                # -----------------------------
                # KPI TOTALS
                # -----------------------------

                total_forecasted_demand += (
                    seven_day_forecast
                )

                total_recommended_order += (
                    recommended_order
                )

                # -----------------------------
                # STORE PRODUCT RESULT
                # -----------------------------

                inventory_results.append({
                    "Product ID": product_id,
                    "Current Stock": int(
                        latest_stock
                    ),
                    "7-Day Forecast": int(
                        seven_day_forecast
                    ),
                    "Reorder Point": int(
                        reorder_point
                    ),
                    "Recommended Order": int(
                        recommended_order
                    ),
                    "Risk Status": status
                })

        # -----------------------------
        # BUSINESS KPIs
        # -----------------------------

        st.subheader("Business KPIs")

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "Total Products",
                total_products
            )

        with col2:

            st.metric(
                "7-Day Forecasted Demand",
                total_forecasted_demand
            )

        with col3:

            st.metric(
                "Products Requiring Reorder",
                products_requiring_reorder
            )

        with col4:

            st.metric(
                "Total Recommended Order",
                int(total_recommended_order)
            )

        # -----------------------------
        # INVENTORY RISK TABLE
        # -----------------------------

        if inventory_results:

            st.subheader(
                "Product Inventory Risk"
            )

            inventory_df = pd.DataFrame(
                inventory_results
            )

            st.dataframe(
                inventory_df,
                use_container_width=True,
                hide_index=True
            )
            
            # Recommended Order Chart
            st.subheader("Recommended Order by Product")

            order_chart = inventory_df.set_index(
                "Product ID"
            )["Recommended Order"]

            st.bar_chart(order_chart)

            # Inventory Risk Summary
            st.subheader("Inventory Risk Summary")

            risk_counts = (
                inventory_df["Risk Status"]
                .value_counts()
                .reindex(
                    [
                        "🔴 Reorder Now",
                        "🟡 Monitor",
                        "🟢 Stock Sufficient"
                    ],
                    fill_value=0
                )
            )

            st.bar_chart(risk_counts)
            # Low Stock Alerts
            st.subheader("⚠️ Low Stock Alerts")

            low_stock = inventory_df[
                inventory_df["Risk Status"] == "🔴 Reorder Now"
            ]

            if not low_stock.empty:
                st.warning(
                    f"{len(low_stock)} products need reordering."
                )
                st.dataframe(
                    low_stock,
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.success("No products currently need reordering.")
            # Download Inventory Report
            st.subheader("📥 Download Inventory Report")

            csv_data = inventory_df.to_csv(index=False).encode("utf-8")

            st.download_button(
                label="Download Inventory Report (CSV)",
                data=csv_data,
                file_name="inventory_report.csv",
                mime="text/csv"
            )


