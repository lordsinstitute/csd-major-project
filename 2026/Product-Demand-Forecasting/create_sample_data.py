import pandas as pd
import random
from datetime import datetime, timedelta

# Starting date
start_date = datetime(2026, 1, 1)

products = [
    {
        "product_id": "P101",
        "product_name": "Wireless Mouse",
        "base_demand": 20,
        "starting_stock": 150,
        "lead_time_days": 3
    },
    {
        "product_id": "P102",
        "product_name": "Mechanical Keyboard",
        "base_demand": 15,
        "starting_stock": 120,
        "lead_time_days": 5
    },
    {
        "product_id": "P103",
        "product_name": "USB-C Hub",
        "base_demand": 10,
        "starting_stock": 100,
        "lead_time_days": 4
    }
]

rows = []

for day in range(30):

    current_date = start_date + timedelta(days=day)

    for product in products:

        # Small random variation in daily demand
        units_sold = max(
            1,
            product["base_demand"] + random.randint(-5, 5)
        )

        # Reduce stock based on sales
        stock_on_hand = max(
            0,
            product["starting_stock"] - (units_sold * day)
        )

        rows.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "product_id": product["product_id"],
            "product_name": product["product_name"],
            "units_sold": units_sold,
            "stock_on_hand": stock_on_hand,
            "lead_time_days": product["lead_time_days"]
        })


df = pd.DataFrame(rows)

df.to_csv("sample_product_sales_30days.csv", index=False)

print("Dataset created successfully!")
print(f"Rows: {len(df)}")
print(df.head())