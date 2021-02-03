# -*- coding: utf-8 -*-
"""
Created on Sun Mar 22 00:36:21 2020

@author: Puran Prakash Sinha
"""

# commect MySQL using connector
import datetime
import mysql.connector

cnx = mysql.connector.connect(user='root', password='Sinha@123',
                              host='localhost',
                              database='org',
                              use_pure=False)

cursor = cnx.cursor()

# querying with using connector
query = ("SELECT * FROM worker where salary>100000")
cursor.execute(query)
ans= cursor.fetchall() 
print(ans)
for i in ans: 
	print(i)


cursor.close()
cnx.close()

