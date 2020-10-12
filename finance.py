import yfinance as yf
import pandas as pd
import numpy as np

import psycopg2 as pg
from psycopg2 import extras, sql
from psycopg2.extensions import register_adapter, AsIs
from psycopg2.extras import execute_values, Json

from datetime import date, timedelta

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

STOCK_STRING = " ".join(STOCKS)

columns = [
    "Date",
    "Open",
    "High",
    "Close",
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
    "Stock": "stock_name",
    "External Unique Identifier": "external_unique_identifier"
}

search_query = '''
    select distinct stock_name
    from financial_data
    '''

# Run SQL Query
cursor = postgres_connection.cursor()

cursor.execute(search_query)
database_stocks = cursor.fetchall()

# postgres_connection.close()

current_stocks = [item[0] for item in database_stocks]

current_stock_string = " ".join(current_stocks)

df = pd.DataFrame(columns=columns)

if not current_stock_string:
    historical_data = yf.Tickers(STOCK_STRING).history(period="max", group_by="ticker")
    for stock in STOCKS:
        filtered_hist_data = historical_data[stock]
        filtered_hist_data.dropna(axis=0, inplace=True, subset=["Open", "Close"])
        filtered_hist_data.reset_index(inplace=True)
        filtered_hist_data.insert(0, "Stock", stock)
        df = pd.concat([df, filtered_hist_data], sort=True, ignore_index=True)
else:
    current_data = yf.download(tickers=STOCK_STRING, group_by="ticker", period="1d")
    for stock in STOCKS:
        filtered_data = current_data[stock]
        filtered_data.reset_index(inplace=True)
        filtered_data.insert(0, "Stock", stock)
        df = pd.concat([df, filtered_data], sort=True, ignore_index=True)

df["Date"] = df["Date"].dt.strftime('%Y-%m-%d')

df["External Unique Identifier"] = df["Stock"] + "|" + df["Date"]

filtered_for_insert = df[
    ["Stock",
    "Date",
    "Open",
    "Close",
    "High",
    "Volume",
    "Dividends",
    "Stock Splits",
    "External Unique Identifier"]
]

renamed = filtered_for_insert.rename(columns=sql_columns)
remove_duplicates = renamed.drop_duplicates(subset='external_unique_identifier')

tuple_list = [tuple(x) for x in remove_duplicates.to_numpy()]

query = '''
        INSERT INTO financial_data (
            stock_name,
            stock_date,
            open_price,
            close_price,
            max_price,
            volume,
            dividends,
            stock_splits,
            external_unique_identifier
        ) VALUES %s
        ON CONFLICT (external_unique_identifier) DO UPDATE
        SET
            stock_date = EXCLUDED.stock_date,
            open_price = EXCLUDED.open_price,
            max_price = EXCLUDED.max_price,
            volume = EXCLUDED.volume,
            dividends = EXCLUDED.dividends,
            stock_splits = EXCLUDED.stock_splits,
            stock_name = EXCLUDED.stock_name
        RETURNING id
        '''

# Run SQL Query
# cursor = postgres_connection.cursor()

with cursor as conn:
    pg.extras.execute_values(conn, query, tuple_list)
    postgres_connection.commit()
    conn.close()

# Close the Connection
postgres_connection.close()