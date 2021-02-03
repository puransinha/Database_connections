#!/usr/bin/env python
# coding: utf-8


#Database Connection

**********************************************************************




import cx_Oracle
import datetime

try:
    # Connect to Oracle
    connstr = 'refer above'
    conn = cx_Oracle.connect(connstr)
    cur = conn.cursor()
    print("Connection is successful")
except:
    print("Unable to Connect")

# Execution Start time

Start_time = datetime.datetime.now()
print(Start_time)

# exporting data
try:
    cursor = oracle_conn.cursor()
    print('executing the query in Oracle server...')
    cursor.execute(sql_query)

    # column names in lowercase because it's case sensitive
    ora_column_names = [col[0].lower() for col in cursor.description]

    # export rows fetching 'num_rows_fetch' every time
    print('start exporting data...')
    rows = cursor.fetchmany(num_rows_fetch)
    while len(rows) > 0:
        # convert rows to a list of dicts
        mongo_rows = [dict(zip(ora_column_names, row)) for row in rows]

        # "Transform" the rows
        if transform:
            mongo_rows = transform(mongo_rows)


# In[ ]:


***** Calling REST URL *******




import requests
import json
import collections
import cx_Oracle
import datetime
import pandas as pd

#Defining Funtion for Oracle anc will be used later


def Oracle_Call():
   try:
      insert_stmt = 'insert into test_snow(ticket_number,creation_date,short_description) values (:1,:2,:3)'
      cur.execute(insert_stmt,[Number, datetime.datetime.now(),SD])

      conn.commit()
      print(" Records Inserted Successfully")
   except cx_Oracle.DatabaseError as e:
       raise
       print(" Error inserting Records ")



# Set the request parameters
url = 'https://xxxxx.service-now.com/api/now/table/problem?sysparm_limit=10'

# Pass User Name and password
user = 'user'
pwd = 'password'

# Set proper headers
headers = {"Content-Type": "application/json", "Accept": "application/json"}

# Do the HTTP request
response = requests.get(url, auth=(user, pwd), headers=headers)

# Check for HTTP codes other than 200
if response.status_code != 200:
   print('Status:', response.status_code, 'Headers:',
         response.headers, 'Error Response:', response.json())
   exit()

# Decode the JSON response into a dictionary and use the data
#print (my_dict)
data = response.json()

new_data = pd.DataFrame([data])
print(new_data)

#Connect to Oracle 

#Execution Start time  

Start_time =  datetime.datetime.now()

try:
    # Connect to Oracle 
    connstr='user/pwd@localhost.xx.net:1532/SID'
    conn = cx_Oracle.connect(connstr)
    cur = conn.cursor()
    print("Connection is successful")
except:
    print("Unable to Connect")

for x in data['result']:
   Number = x['number']
   SD = x['short_description']

   
   print(Number)
   try:
      insert_stmt = 'insert into test_snow(ticket_number,creation_date,short_description) values (:1,:2,:3)'
      cur.execute(insert_stmt,[Number, datetime.datetime.now(),SD])

      conn.commit()
      print(" Records Inserted Successfully")
   except cx_Oracle.DatabaseError as e:
       raise
       print(" Error inserting Records ") 


#Execution Completion time  

Complete_time =  datetime.datetime.now()

print("Start_time : "  , Start_time)
print("Complete_time : "  , Complete_time)





