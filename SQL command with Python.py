# -*- coding: utf-8 -*-
"""
Created on Thu Mar 19 23:04:39 2020

@author: Puran Prakash Sinha
"""


# Python code to demonstrate table creation and  
# insertions with SQL 
  
# importing module 
import sqlite3 
  
# connecting to the database  
connection = sqlite3.connect("org.db") 
  
# cursor  
crsr = connection.cursor() 
# sql_command='''drop TABLE ato;'''  
# SQL command to create a table in the database 
# CREATE TABLE IF NOT EXISTS (check duplicates)
sql_command = """CREATE TABLE emp (  
staff_number INTEGER PRIMARY KEY,  
fname VARCHAR(20),  
lname VARCHAR(30),  
gender CHAR(1),  
joining DATE);"""

# execute the statement 
crsr.execute(sql_command) 

# SQL command to insert the data in the table 
sql_command = """INSERT INTO emp VALUES (23, "Rishabh", "Bansal", "M", "2014-03-28");"""
crsr.execute(sql_command)
  
# another SQL command to insert the data in the table 
sql_command = """INSERT INTO emp VALUES (1, "Bill", "Gates", "M", "1980-10-28");"""
crsr.execute(sql_command) 
  
# To save the changes in the files. Never skip this.  
# If we skip this, nothing will be saved in the database. 
connection.commit() 




# Python code to demonstrate SQL to fetch data. 

# execute the command to fetch all the data from the table emp 
crsr.execute("SELECT * FROM emp") 

# store all the fetched data in the ans variable 
ans= crsr.fetchall() 

# loop to print all the data 
for i in ans: 
	print(i) 

# close the connection 
connection.close() 

import csv


#crsr=cnxn.cursor() # Get the cursor
csv_data = csv.reader(r'D:\Data Science-Main\Python\auto.csv') # Read the csv
csv_data
print(csv_data)
