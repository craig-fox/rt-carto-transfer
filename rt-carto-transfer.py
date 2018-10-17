from __future__ import print_function
from carto.auth import APIKeyAuthClient
from carto.exceptions import CartoException
from carto.sql import SQLClient
from carto.datasets import DatasetManager
from carto.file_import import FileImportJobManager
from itertools import *
import psycopg2
import json
import csv
import asyncio
import sys
import time

def connectToAWSDb():
    print("Host {}, db {}, user {}".format(config['mysql']['host'], config['mysql']['db'], config['mysql']['user']))
    db = psycopg2.connect(host=config['mysql']['host'],
                      database=config['mysql']['db'],
                      user=config['mysql']['adminuser'],
                      password=config['mysql']['adminpassword'])
    print("Connected to AWS database {name}".format(name=config['mysql']['db']))
    return db

def writeCSVFromTable(task, target):
    name = task['name']
    template = task['template']
    sql = template.format(target=target)
    print("{} SQL".format(sql))
    number_of_rows = cursor.execute(sql)
    columns = [i[0] for i in cursor.description]
    result = cursor.fetchall()
    csvName = 'csv/' + name + '.csv'
    with open(csvName, 'w', newline='') as fp:
        a = csv.writer(fp, delimiter=',')
        a.writerow(columns)
        a.writerows(result)
    print("{} csv written".format(name))

async def createCartoDataset(name):
    try:
       csv_file = './csv/{name}.csv'.format(name=name)
       dataset = dataset_manager.create(csv_file)
       print('Created dataset {name} with id {id}'.format(name=dataset.name,id={dataset.id}))
    except CartoException as e:
        print("some error ocurred", e)

def processTasks(tasks, target):
    carto_tasks = []
    for task in tasks:
        name = task['name']
        carto_tasks.append(asyncio.ensure_future(createCartoDataset(name)))
        writeCSVFromTable(task, target)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait(carto_tasks))
    loop.close()

def createTable(script):
    #print("the script is {script}".format(script=script))
    table_sql = script
    runScript(table_sql)
    print("Table created")
    carto_sql = "SELECT cdb_cartodbfytable('ryanjudd', '{}')".format(target)
    #print("the script is {script}".format(script=carto_sql))
    runScript(carto_sql)
    print("Table adapted for Carto")

def maxCartoId():
    cartoid_sql = "SELECT MAX(cartodb_id) FROM {}".format(target)
    #print("the script is {script}".format(script=cartoid_sql))
    data = runScript(cartoid_sql)
    return data['rows'][0]['max'] or 0

def pause(secs):
    print("Pausing script execution for {} seconds".format(secs))
    time.sleep(secs)

def rateSeconds():
    times = next(counter)
    seconds = 10 + (5* (times // 3))
    print("Now pausing for {}".format(seconds))
    return seconds

def dropTempTables(tables):
    for table in tables:
        print("Dropping temp table {}".format(table))
        delete_sql = "DROP TABLE {}".format(table)
        runScript(delete_sql)
        pause(10)
    print("All temp tables dropped")


def runScript(script):
    data = None
    while True:
        try:
            data = carto_sql_client.send(script)
            break
        except CartoException as e:
            script_error = str(e)
            print("some error ocurred", script_error)
            if script_error == "Rate limit exceeded":
                print("Slowing down to reduce rate limit")
                pause(rateSeconds())
                continue
            else:
                print("Could not resolve error")
                break
    return data

def insertIntoTable(script, source, row_filter):
    max_carto_dbid = maxCartoId()
    insert_sql = script.format(source=source, maxid=max_carto_dbid)
    insert_sql = insert_sql + " {row_filter} ".format(row_filter=row_filter)
    print("Inserting rows with filter: {}".format(row_filter))
    data = runScript(insert_sql)
    pause(10)
    return data

def transferData():
    with open(process['scripts']['create'].format(target=target), 'r') as create_file:
        create_sql = create_file.read()
    with open(process['scripts']['insert'].format(target=target), 'r') as insert_file:
        insert_sql = insert_file.read()
    pause(20)
    createTable(create_sql)

    total_rows = None
    row_filter = None
    lower_limit = None
    upper_limit = None
    data = None
    CHUNK = 100000

    for table in temp_tables:
        print("Transferring data for {}".format(table))
        total_rows = None
        while total_rows == None or total_rows == CHUNK:
            if total_rows == None:
                upper_limit = CHUNK
                row_filter = "AND cartodb_id <= {upper_limit}".format(upper_limit=upper_limit)
                data = insertIntoTable(insert_sql, table, row_filter)
                total_rows = data['total_rows']
                print("Returned {} rows".format(total_rows))
            elif total_rows == CHUNK:
                lower_limit = upper_limit
                upper_limit = upper_limit + CHUNK
                row_filter = " AND cartodb_id > {lower} AND cartodb_id <= {upper}".format(upper=upper_limit, lower=lower_limit)
                data = insertIntoTable(insert_sql, table, row_filter)
                total_rows = data['total_rows']
                print("Returned {} rows".format(total_rows))

config = None
process = None
db = None
counter = count(1)

with open('config.json') as json_data_file:
    config = json.load(json_data_file)
process_file_name = sys.argv[1]
with open('./{file}'.format(file=process_file_name)) as json_process_file:
    process = json.load(json_process_file)
db = connectToAWSDb()

USERNAME=config['carto']['account']
USR_BASE_URL = config['carto']['url_base'].format(user=USERNAME)
auth_client = APIKeyAuthClient(api_key=config['carto']['api'], base_url=USR_BASE_URL)
cursor = db.cursor()
dataset_manager = DatasetManager(auth_client)
carto_sql_client = SQLClient(auth_client)

target = process['target']
temp_tables = process['temp_tables']
tasks = process['tasks']
processTasks(tasks, target)

print("Closing AWS database")
db.close()
transferData()
dropTempTables(temp_tables)
