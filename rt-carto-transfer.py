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

def writeCSVFromTable(name):
    sql_template = config[sql_template]
    sql = sql_template.format(name)
    number_of_rows = cursor.execute(sql)
    result = cursor.fetchall()
    csvName = 'csv/' + name + '.csv'
    with open(csvName, 'w', newline='') as fp:
        a = csv.writer(fp, delimiter=',')
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
    
    
config = None
with open('config.json') as json_data_file:
    config = json.load(json_data_file)
db = None
db = psycopg2.connect(host=config['mysql']['host'],
                      database=config['mysql']['db'],
                      user=config['mysql']['user'],
                      password=config['mysql']['password'])
print("Connected to AWS database {name}".format(name=config['mysql']['db']))

USERNAME=config['carto']['account']
USR_BASE_URL = config['carto']['url_base'].format(user=USERNAME)
auth_client = APIKeyAuthClient(api_key=config['carto']['api'], base_url=USR_BASE_URL)

cursor = db.cursor()
tasks = config['tasks']
dataset_manager = DatasetManager(auth_client)

datasets = dataset_manager.all()

carto_tasks = []
for task in tasks:
    name = task['name']
    ds_id = getDatasetId(name, datasets)
    if ds_id:
        deleteDataset(ds_id, name)
    writeCSVFromTable(name)
    carto_tasks.append(asyncio.ensure_future(createCartoDataset(name)))

loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.wait(carto_tasks))  
loop.close()
    
print("Closing database") 
db.close()
