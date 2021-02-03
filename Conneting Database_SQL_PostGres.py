# -*- coding: utf-8 -*-
"""
Created on Tue Sep 22 23:32:08 2020

@author: Puran Prakash Sinha
"""
#Connection for SQL

import mysql.connector

def get_connection():
    connection=mysql.connector.connect(host='localhost',
                                       database='org',
                                       user='root',
                                       password='Sinha@123')
    return connection

def connection_close(connection):
    if connection:
        connection.close()

def read_db():
    try:
        connection=get_connection()
        cursor=connection.cursor()
        cursor.execute("Select version();")
        db_version=cursor.fetchone()
        print('you are connected to SQL', db_version)
        connection_close(connection)
    except(Exception, mysql.connector.Error)as error:
        print('Error while connecting',error)
print('print version')
read_db()

# connection for PostGres


import psycopg2

def get_connection():
    connection = psycopg2.connect(user="postgres",
                                  password="pynative@#29",
                                  host="127.0.0.1",
                                  port="5432",
                                  database="python_db")
    return connection

def close_connection(connection):
    if connection:
        connection.close()

def read_database_version():
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        print("You are connected to PostgreSQL version: ", db_version)
        close_connection(connection)
    except (Exception, psycopg2.Error) as error:
        print("Error while getting data", error)

print("Print Database version")
read_database_version()