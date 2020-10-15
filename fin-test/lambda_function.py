  
import yfinance as yf
import pandas as pd
import os

import psycopg2 as pg
from psycopg2 import extras, sql
from psycopg2.extensions import register_adapter, AsIs
from psycopg2.extras import execute_values, Json

import json

#UTILITY FUNCTIONS
def connect_postgres():
    """
    Connects to AWS RDS postgres database
    """
    postgres_connection = pg.connect(
        host = os.environ.get('HOST'),
        database= "postgres",
        user="postgres",
        password=os.environ.get('PASSWORD')
    )
    cursor = postgres_connection.cursor()
    return (postgres_connection, cursor)


def get_stocks_in_database(cursor):
    search_query = '''
        select distinct stock_name
        from financial_data
        '''
    cursor.execute(search_query)
    database_stocks = cursor.fetchall()

    current_stocks = [item[0] for item in database_stocks]

    return current_stocks

def get_stock_data(cursor):
    search_query = '''
        SELECT *
        FROM financial_data WHERE (stock_name, stock_date) IN (
            SELECT stock_name, MAX(stock_date) AS stock_date
            FROM financial_data
            GROUP BY stock_name
        )
        ORDER BY stock_name
    '''
    cursor.execute(search_query)
    database_stocks = cursor.fetchall()
    
    return database_stocks

#LAMBDA FUNCTIONS
def get_all_data(event, context):
    """
    Lambda Function get-all-data
    Returns all tickers with corresponding data
    """
    postgres_connection, cursor = connect_postgres()

    data = get_stock_data(cursor)

    postgres_connection.close()

    return {
        'statusCode': 200,
        'headers': { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': '*' },
        'body': json.dumps(data, default=lambda x: x.__str__())
    }

def get_all_tickers(event, context):
    """
    Lambda Function get-all-tickers
    Returns list of all tickers in the table.
    """
    postgres_connection, cursor = connect_postgres()

    current_stocks = get_stocks_in_database(cursor)

    postgres_connection.close()

    return {
        'statusCode': 200,
        'headers': { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': '*' },
        'body': json.dumps(current_stocks)
    }


def lambda_handler(event, context):
    """
    Lambda Function fin-test
    Adds tickers specified in queryStringParameters to table and updates all for current data.
    Runs on stock market close and HTTP call.
    """
    if 'tickers' in event['queryStringParameters']:
        tickers = event['queryStringParameters']['tickers']
        STOCKS = [stock.upper() for stock in tickers.split(',')]
    else:
        #Shouldn't be hardcoded. Does this script already update all preexisting stocks in the db?
        STOCKS = ['AMZN', 'NLOK']
    
    # Start the Database Connection
    postgres_connection, cursor = connect_postgres()

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

    def get_historical_data(df, database_stocks, stocks):
        current_stock_string = " ".join(database_stocks)

        if current_stock_string:
            historical_data = yf.Tickers(current_stock_string).history(period="max", group_by="ticker")
            for stock in stocks:
                filtered_hist_data = historical_data[stock]
                filtered_hist_data.dropna(axis=0, inplace=True, subset=["Open", "Close"])
                filtered_hist_data.reset_index(inplace=True)
                filtered_hist_data.insert(0, "Stock", stock)
                df = pd.concat([df, filtered_hist_data], sort=True, ignore_index=True)

        return df

    def get_data(df, stocks):
        current_data = yf.download(tickers=STOCK_STRING, group_by="ticker", period="1d")
        for stock in stocks:
            filtered_data = current_data[stock]
            filtered_data.reset_index(inplace=True)
            filtered_data.insert(0, "Stock", stock)
            df = pd.concat([df, filtered_data], sort=True, ignore_index=True)

        return df

    df = pd.DataFrame(columns=columns)

    # Find all Stocks currently in Database
    stocks_in_db = get_stocks_in_database(cursor)

    historical_data_to_get = list()
    for stock in STOCKS:
        if stock not in stocks_in_db:
            historical_data_to_get.append(stock)

    # Get historical data for stocks not currently in the database
    if historical_data_to_get:
        if len(historical_data_to_get) > 1:
            current_stock_string = " ".join(historical_data_to_get)
            historical_data = yf.Tickers(current_stock_string).history(period="max", group_by="ticker")
        else:
            current_stock_string = historical_data_to_get[0]
            historical_data = yf.Ticker(current_stock_string).history(period="max", group_by="ticket")

        for stock in historical_data_to_get:
            filtered_hist_data = historical_data[stock]
            filtered_hist_data.dropna(axis=0, inplace=True, subset=["Open", "Close"])
            filtered_hist_data.reset_index(inplace=True)
            filtered_hist_data.insert(0, "Stock", stock)
            df = pd.concat([df, filtered_hist_data], sort=True, ignore_index=True)

    # Get today's data for all stocks
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
    with cursor as conn:
        pg.extras.execute_values(conn, query, tuple_list)
        postgres_connection.commit()
        conn.close()

    # Close the Connection
    postgres_connection.close()

    return {
        'statusCode': 200,
        'headers': { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': '*' },
        'body': json.dumps('The following stocks have been updated: ' + STOCK_STRING)
    }