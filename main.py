import requests
import json
import pprint
import re
import os
import urllib3
from codec.actions import get_status, get_last, get_sip, get_people, get_loss, get_diag, get_all
from influxdb import InfluxDBClient
import threading
import datetime


def flattening(nested, prefix, ignore_list):
    field = {}

    flatten(True, nested, field, prefix, ignore_list)

    return field

def flatten(top, nested, flatdict, prefix, ignore_list):
    def assign(newKey, data, toignore):
        if toignore:
            if isinstance(data, (dict, list, tuple,)):
                json_data = json.dumps(data)
                flatdict[newKey] = json_data
            else:
                flatdict[newKey] = data
        else:
            if isinstance(data, (dict, list, tuple,)):
                flatten(False, data, flatdict, newKey, ignore_list)
            else:
                flatdict[newKey] = data

    if isinstance(nested, dict):
        for key, value in nested.items():
            ok = match_key(ignore_list, key)
            if ok and prefix == "":
                assign(key, value, True)
            elif ok and prefix != "":
                newKey = create_key(top, prefix, key)
                assign(newKey, value, True)
            else:
                newKey = create_key(top, prefix, key)
                assign(newKey, value, False)

    elif isinstance(nested, (list, tuple,)):
        for index, value in enumerate(nested):
            if isinstance(value, dict):
                for key1, value1 in value.items():
                    ok = match_key(ignore_list, key1)
                    if ok:
                        subkey = str(index) + "." + key1
                        newkey = create_key(top, prefix, subkey)
                        assign(newkey, value1, True)
                    else:
                        newkey = create_key(top, prefix, str(index))
                        assign(newkey, value, False)
                        
            else:
                newkey = create_key(top, prefix, str(index))
                assign(newkey, value, False)
                
                
    else:
        return ("Not a Valid input")

def create_key(top, prefix, subkey):
    key = prefix
    if top:
        key += subkey
    else:
        key += "." + subkey

    return key				


def match_key(ignorelist, value):
    for element in ignorelist:
        if element == value:
            return True 
    
    return False

def build_data_array(host, location, msg, time, ignorelist):
    msg = json.loads(msg)

    field = flattening(msg, "", ignorelist)
    
    if "Status.@version" in field:
        os = field['Status.@version']
    else:
        os = "unknown"
        
    if "Status.SystemUnit.ProductId" in field:
        model = field['Status.SystemUnit.ProductId']
    else:
        model = "unknown"
        
    if not location:
        location = 'UNKNOWN'
        

    json_body = {
        "measurement": 'codec_stats',
        "tags": {
            'hostname': host,
            'os': os,
            'model': model,
            'location': location
        },
        'time': time,
        "fields": field
    }
    
    # Objects that should be Integers
    int_objects = ['HardwareID','Tilt','ScreenSize','VlanId','Pan','HardwareInfo','Widget','PeopleCount']	
    
    for attr, value in json_body['fields'].items():
        if any(vals in attr for vals in int_objects):
            if value.isnumeric() == False:
                json_body['fields'][attr] = 0
        if value.isnumeric():
            json_body['fields'][attr] = int(value)
        
    return json_body


# Check status of codecs
def check_status():
    # Get batched timestamp
    d = datetime.datetime.now()
    dUTC = datetime.datetime.utcnow()
    # Run every 6 mins
    threading.Timer(360.0, check_status).start()
    headers = {
            'X-Auth-Token': '984711fdc0f7c9d86aa38585db979373',
            }

    r = requests.get('http://170.2.96.200/api/v0/devices', headers=headers)
    librenms_devices = json.loads(r.text)
    
    # filter out by codec
    keyValList = ['vccodec']
    expectedResult = [d for d in librenms_devices['devices'] if d['os'] in keyValList]
    
    points = []
    
    print("Starting codec batch job: " + str(d))
    
    for codec in expectedResult:
        allstats = get_all(codec['hostname'])
        if (allstats):
            data = json.dumps(allstats).replace('null', '""')
            # List keys you dont want flatten
            ignore = ["floatdata", "key2"]
            points.append(build_data_array(codec['hostname'],codec['location'], data,dUTC, ignore))
    
    try:
        client = InfluxDBClient('170.2.96.200', 8086, '', '', 'codecs')
        client.write_points(points,batch_size=100000)    
    except Exception as e:
        print(e)
        
    print("Finished codec batch job: " + str(d))
        
check_status()