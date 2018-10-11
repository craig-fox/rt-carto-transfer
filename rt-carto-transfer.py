from __future__ import print_function
from carto.auth import APIKeyAuthClient
from carto.exceptions import CartoException
from carto.sql import SQLClient
from carto.datasets import DatasetManager
from carto.file_import import FileImportJobManager
import psycopg2
import json
import csv
import asyncio
import sys

def writeCSVFromTable(task):
    name = task['name']
    try:
        sql_template = task['template']
    except KeyError:
        sql_template = config['sql_template']
   
    print("{} SQL template ".format(sql_template))
    try:
        table_name = task['table_name']
    except KeyError:
        table_name = name

    print("Table Name {}".format(table_name))
   
    sql = sql_template.format(table_name)
    number_of_rows = cursor.execute(sql)
    columns = [i[0] for i in cursor.description]
    result = cursor.fetchall()
    csvName = 'csv/' + name + '.csv'
    with open(csvName, 'w', newline='') as fp:
        a = csv.writer(fp, delimiter=',')
        a.writerow(columns)
        a.writerows(result)
    print("{} csv written".format(name))

def deleteDataset(id, name):
    dataset = dataset_manager.get(id)
    dataset.delete()
    print('Dataset {name} deleted'.format(name=name))

def getDatasetId(name, sets):
    ds_iter = filter(lambda ds: ds.name==name, sets)
    ds_id = None
    for ds in ds_iter:
        ds_id = ds.id
        break
    return ds_id

async def createCartoDataset(name):
    try:
       csv_file = './csv/{name}.csv'.format(name=name)
       dataset = dataset_manager.create(csv_file)
       print('Created dataset {name} with id {id}'.format(name=dataset.name,id={dataset.id}))
    except CartoException as e:
        print("some error ocurred", e)

async def runCartoImport(name):
    try:
       csv_file = './csv/{name}.csv'.format(name=name)
       file_import_manager = FileImportJobManager(auth_client)
       file_import = file_import_manager.create(csv_file)
       file_id = file_import.get_id()
     #  file_name = file_import.get_table_name()
       print("Importing file {name} with id {id}".format(name=name, id={file_id}))
       file_import.run()
       while(file_import.state != "complete" and file_import.state != "created" and file_import.state != "success"):
           time.sleep(20)
           file_import.refresh()
           print("Importing with state {state}").format(state=file_import.state)
           if (file_import.state == 'failure'):
               print('The error code is: ' + str(file_import))
               break
       if(file_import_state == "complete"):
           print('Imported file {name} with id {id}'.format(name=name,id={file_id}))
       else:
           print('File {name} failed with import state {state}'.format(name=name, state=file_import_state))
    except CartoException as e:
        print("some error ocurred", e)
    
config = None
tasks = None
with open('config.json') as json_data_file:
    config = json.load(json_data_file)
tasks_file_name = sys.argv[1]
with open('./tasks/{file}'.format(file=tasks_file_name)) as json_tasks_file:
    tasks = json.load(json_tasks_file)
db = None
print("Host {}, db {}, user {}, password {}".format(config['mysql']['host'], config['mysql']['db'], config['mysql']['user'], config['mysql']['password']))
db = psycopg2.connect(host=config['mysql']['host'],
                      database=config['mysql']['db'],
                      user=config['mysql']['adminuser'],
                      password=config['mysql']['adminpassword'])
print("Connected to AWS database {name}".format(name=config['mysql']['db']))

USERNAME=config['carto']['account']
USR_BASE_URL = config['carto']['url_base'].format(user=USERNAME)
auth_client = APIKeyAuthClient(api_key=config['carto']['api'], base_url=USR_BASE_URL)

cursor = db.cursor()
tasks = tasks['tasks']
dataset_manager = DatasetManager(auth_client)

datasets = dataset_manager.all()

carto_tasks = []
for task in tasks:
    name = task['name']
    ds_id = getDatasetId(name, datasets)
    #if ds_id:
    #    deleteDataset(ds_id, name)
    writeCSVFromTable(task)
    carto_tasks.append(asyncio.ensure_future(createCartoDataset(name)))
    #carto_tasks.append(asyncio.ensure_future(runCartoImport(name)))

loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.wait(carto_tasks))  
loop.close()
    
print("Closing database") 
db.close()
