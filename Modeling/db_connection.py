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
        host="finance-models.cvcg7dv0e6gx.us-east-2.rds.amazonaws.com",
        database="postgres",
        user="postgres",
        password="qUbzNkT2CIdHFoxgyWJn"
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

def query(cursor, search_query):
    cursor.execute(search_query)
    response = cursor.fetchall()

    return response

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