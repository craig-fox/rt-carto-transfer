from __future__ import print_function
import boto
import psycopg2
import csv
import json
import requests

def writeCSVFromTable(name):
    sql_template = "SELECT * FROM {} LIMIT 5"
    sql = sql_template.format(name)
    number_of_rows = cursor.execute(sql)
    result = cursor.fetchall()
    csvName = 'csv/' + name + '.csv'
    with open(csvName, 'w', newline='') as fp:
        a = csv.writer(fp, delimiter=',')
        a.writerows(result)
    print("{} csv written".format(name))

def writeToCarto(name):
    url_template = 'https://{hostname}.carto.com/api/v1/imports/?api_key={api}'
    url = url_template.format(hostname=data['carto']['account'], api=data['carto']['api'])
    print(url)
    csv = 'csv/' + name + '.csv'
    r_json = None
    with open(csv,'r') as f:
      r = requests.post(url, files={csv:f})
      r_json = r.json()
    print(r_json)
    queued_item = (name, r_json['item_queue_id'])
    print(queued_item)
    return queued_item
   
def readProgress(name, item_id):
    url_template = 'https://{hostname}.carto.com/api/v1/imports/{item_id}?api_key={api}'
    url = url_template.format(hostname=data['carto']['account'], item_id=item_id, api=data['carto']['api'])
    print(url)
    
    

with open('config.json') as json_data_file:
    data = json.load(json_data_file)

print(data['mysql']['host'])

db = None
db = psycopg2.connect(host=data['mysql']['host'],
                      database=data['mysql']['db'],
                      user=data['mysql']['user'],
                      password=data['mysql']['password'])
print("Connected to database")

cursor = db.cursor()
tasks = data['tasks']
item_queue = []

#for task in tasks:
#    writeCSVFromTable(task['name'])

for task in tasks:
    queued_item = writeToCarto(task['name'])
    item_queue.append(queued_item)
    
print("Closing database") 
db.close()
