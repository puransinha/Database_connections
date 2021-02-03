# -*- coding: utf-8 -*-
"""
Created on Wed Nov 18 23:31:12 2020

@author: Puran Prakash Sinha
"""

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