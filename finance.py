import yfinance as yf
import pandas as pd
import numpy as np

import psycopg2 as pg
from psycopg2 import extras, sql
from psycopg2.extensions import register_adapter, AsIs
from psycopg2.extras import execute_values, Json

postgres_connection = pg.connect(
    host = "finance-models.cvcg7dv0e6gx.us-east-2.rds.amazonaws.com",
    database= "postgres",
    user="postgres",
    password="qUbzNkT2CIdHFoxgyWJn"
)


STOCKS = [
    "AMZN",
    "NLOK"
]

columns = [
    "Date",
    "Open",
    "High",
    "Volume",
    "Dividends",
    "Stock Splits",
    "Stock"
]

sql_columns = {
    "Date": "stock_date",
    "Open": "open_price",
    "High": "max_price",
    "Volume": "volume",
    "Dividends": "dividends",
    "Stock Splits": "stock_splits",
    "Stock": "stock_name"
}

df = pd.DataFrame(columns=columns)

for stock in STOCKS:
    df2 = yf.Ticker(stock).history(period="max")
    df2["Stock"] = stock
    df2.reset_index(inplace=True)
    df = pd.concat([df, df2], sort=True, ignore_index=True)

df["Date"] = df["Date"].dt.strftime('%Y-%m-%d')

filtered_for_insert = df[
    ["Date",
    "Open",
    "High",
    "Volume",
    "Dividends",
    "Stock Splits",
    "Stock"]
]

renamed = filtered_for_insert.rename(columns=sql_columns)

tuple_list = [tuple(x) for x in renamed.to_numpy()]

query = '''
        INSERT INTO financial_data (
            stock_date,
            open_price,
            max_price,
            volume,
            dividends,
            stock_splits,
            stock_name
        ) VALUES %s
        '''

# Run SQL Query
cursor = postgres_connection.cursor()

with cursor as conn:
    pg.extras.execute_values(conn, query, tuple_list)
    postgres_connection.commit()
    conn.close()

# Close the Connection
postgres_connection.close()