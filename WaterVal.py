# -u 7478601330 -p 3e%4p%2e#7 -ni 00000764702c1ffffe547686 -ct LoRa -ae 9999991000000764

#firebase 
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
db_url = 'https://firstproject-afb38.firebaseio.com/'
cred = credentials.Certificate("firstproject-afb38-firebase-adminsdk-r6fpm-9c4723acd5.json")
default_app = firebase_admin.initialize_app(cred, {'databaseURL':db_url})


#predict_water_val
import pandas as pd
from statsmodels.tsa.arima_model import ARIMA


#hex_sym_calculate
import numpy as np

index = ['0','1','2','3','4','5','6','7','8','9','A','B','C','D','E','F']
dic=['0','1','2','3','4','5','6','7','8','9','0A','0B','0C','0D','0E','0F']

for x in range (1,8,1):
    for y in index:
        dic.append('{}{}'.format(x,y))
           
symbol = ['NUL','SOH','STX','ETX','EOT','ENQ','ACK','BEL','BS','HT',
'LF','VT','FF','CR','SO','SI','DLE','DC1','DC2','DC3','DC4','NAK','SYN',
'ETB','CAN','EM','SUB','ESC','FS','GS','RS','US','NULL','NULL','!','/','#',
'$','%','&','//','(',')','*','+',',','-','.','/','0','1','2','3','4','5','6',
'7','8','9',':',';','<','=','>','?','@','A','B','C','D','E','F','G','H','I','J',
'K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','[','/',']','^',
'_','\'','a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r',
's','t','u','v','w','x','y','z','{','|','}','~']

dic = np.asarray(dic)

def calculate(index,data):
    result =data.split('2c')
    string =result[index]
    
    if len(string) == 2:
        find_index = np.where(dic == string)
        cal = symbol[list(find_index[0])[0]+1]
    elif len(string) == 4:
        string1 = string[0:2]
        string2 = string[2:4]
        find_index1 = np.where(dic == string1)
        find_index2 = np.where(dic == string2)
        cal1 = symbol[list(find_index1[0])[0]+1]
        cal2 = symbol[list(find_index2[0])[0]+1]
        cal =cal1+cal2
    if len(string) == 6:
        string1 = string[0:2]
        string2 = string[2:4]
        string3 = string[4:6]
        find_index1 = np.where(dic == string1)
        find_index2 = np.where(dic == string2)
        find_index3 = np.where(dic == string3)
        cal1 = symbol[list(find_index1[0])[0]+1]
        cal2 = symbol[list(find_index2[0])[0]+1]
        cal3 = symbol[list(find_index3[0])[0]+1]
        cal =cal1+cal2+cal3
    h = format(int(cal),'x')
    return int(h)


#ThinPlug
import sys
import argparse
import logging

import http.client
import json
import random
import paho.mqtt.client as mqtt

DEFAULT_TP_HTTP_PORT = 9000
DEFUALT_TP_HTTPS_PORT = 9443

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

class ThingPlug(object):
    def __init__(self, host, port):
        self.app_eui = ''
        self.ukey = ''
        self.user_id = ''
        self.user_pw = ''
        self.mqtt_client_id = ''
        self.host = host
        self.port = port
        self.deviceList = []
        self.deviceCnt = 0
        self.mqttc = None
        self.mqttc_thread = None
        return

    def __del__(self):
        self.mqttDisconnect()

    def http_connect(self):
        if self.port == DEFAULT_TP_HTTP_PORT:
            self.conn = http.client.HTTPConnection(self.host, self.port)  # For Python3.x
        else:
            self.conn = http.client.HTTPSConnection(self.host, self.port)  # For Python3.x

    def http_close(self):
        self.conn.close()

    def thingplugHttpReq(self, req_msg, resp_status):
        json_body = {}

        self.http_connect()
        self.conn.request(req_msg['method'], req_msg['query'], req_msg['payload'], req_msg['header'])
        resp_data = self.conn.getresponse()

        if resp_data.status != resp_status:
            logging.warning('status :' + str(resp_data.status))
            logging.warning(resp_data.msg)
            self.http_close()
            return False

        body = resp_data.read()

        if len(body) != 0:
            json_body = json.loads(body.decode())  # For Python3.x

        self.http_close()

        if 'result_code' in json_body.keys() and json_body['result_code'] != '200':
            logging.warning("ThingPlugHttpReq Fail[result code : " + json_body['result_code'] + "]")
            return False

        return json_body

    def login(self, user_id, user_pw):
        self.user_id = user_id
        self.user_pw = user_pw
        self.ukey = ""

        header = {"password": self.user_pw,
                  "user_id": self.user_id,
                  "Accept": "application/json"
                  }

        query = "/ThingPlug?division=user&function=login"
        req_msg = {'method': "PUT", 'header': header, 'query': query, 'payload': ''}

        json_body = self.thingplugHttpReq(req_msg, 200)
        if json_body == False:
            return False

        self.ukey = json_body['userVO']['uKey']
        logging.info("Login Success")

        return True

    def getDeviceList(self):
        if len(self.ukey) == 0:
            logging.warning('Invalid user key')
            return False, None, None

        header = {"uKey": self.ukey,
                  "Accept": "application/json"
                  }

        query = "/ThingPlug?division=searchDevice&function=myDevice&startIndex=1&countPerPage=1"
        req_msg = {'method': "GET", 'header': header, 'query': query, 'payload': ''}
        json_body = self.thingplugHttpReq(req_msg, 200)
        if json_body == False:
            return False, None, None

        self.deviceCnt = json_body['total_list_count']

        countPerPage = 10
        self.deviceList = []
        reqCnt = int(self.deviceCnt) / countPerPage
        idxCnt = countPerPage

        if (int(self.deviceCnt) % countPerPage != 0):
            reqCnt += 1
            reminder = int(self.deviceCnt) % countPerPage
        else:
            reminder = 0

        # for i in range(reqCnt):          # For Python2.x
        for i in range(int(reqCnt)):  # For Python3.x
            query = "/ThingPlug?division=searchDevice&function=myDevice&startIndex="
            query += str((i * countPerPage) + 1)
            query += "&countPerPage="
            query += str(countPerPage)

            req_msg = {'method': 'GET', 'header': header, 'query': query, 'payload': ''}
            json_body = self.thingplugHttpReq(req_msg, 200)
            if json_body == False:
                return False, None, None

            if ((i == reqCnt - 1) and reminder != 0):
                idxCnt = reminder

            for idx in range(0, idxCnt):
                try:
                    self.deviceList.append(json_body['deviceSearchAPIList'][idx]['device_Id'])
                    logging.info(json_body['deviceSearchAPIList'][idx]['device_Id'])
                except:
                    logging.warning('getDeviceList Fail[error idx : ' + str(idx) + "]")
                    pass

        return True, self.deviceCnt, self.deviceList

    def getLatestData(self, node_id, container):
        if len(self.app_eui) == 0:
            logging.warning('Need to set APP EUI')
            return False, None, None

        header = {"Connection": "keep-alive",
                  "uKey": self.ukey,
                  "X-M2M-Origin": node_id,
                  "X-M2M-RI": node_id + "_" + str(random.randrange(1000, 1100)),
                  "Accept": "application/json"
                  }

        query = "/" + self.app_eui + "/v1_0/remoteCSE-" + node_id + "/container-" + container + "/latest"
        req_msg = {'method': 'GET', 'header': header, 'query': query, 'payload': ''}
        json_body = self.thingplugHttpReq(req_msg, 200)
        if json_body == False:
            return False, None, None

        return True, json_body['cin']['con'], json_body['cin']['lt']

    def createMgmtInstance(self, node_id, mgmtCmd, mgmtMsg):
        if len(self.ukey) == 0:
            logging.warning('Invalid user key')
            return False

        header = {"Accept": "application/json",
                  "X-M2M-Origin": node_id,
                  "X-M2M-RI": node_id + "_" + str(random.randrange(1000, 1100)),
                  "Content-Type": "application/json;ty=12",
                  "uKey": self.ukey
                  }

        # cmd = '{\"cmd\":\"' + mgmtMsg + '\"}'
        payload = {'mgc': {'exra': mgmtMsg, 'exe': 'true', 'cmt': mgmtCmd}}

        query = '/' + self.app_eui + '/v1_0/mgmtCmd-' + node_id + '_' + mgmtCmd
        req_msg = {'method': "PUT", 'header': header, 'query': query, 'payload': json.dumps(payload)}

        json_body = self.thingplugHttpReq(req_msg, 200)
        if json_body == False:
            return False

        self.execInstance = json_body['mgc']['exin'][0]['ri']
        logging.info('MgmtInstance is created')
        return True, self.execInstance

    def retrieveMgmtResult(self, node_id, mgmtCmd, cmdInstance):
        if len(self.ukey) == 0:
            logging.warning('Invalid user key')
            return False

        header = {"Accept": "application/json",
                  "X-M2M-Origin": node_id,
                  "X-M2M-RI": node_id + "_" + str(random.randrange(1000, 1100)),
                  "Content-Type": "application/json;ty=12",
                  "uKey": self.ukey
                  }

        query = '/' + self.app_eui + '/v1_0/mgmtCmd-' + node_id + '_' + mgmtCmd + '/execInstance-' + cmdInstance
        req_msg = {'method': "GET", 'header': header, 'query': query, 'payload': ''}

        json_body = self.thingplugHttpReq(req_msg, 200)
        if json_body == False:
            return False

        self.execStatus = json_body['exin']['exs']
        self.execResult = ''
        if 'exr' in json_body['exin']:
            self.execResult = json_body['exin']['exr']
        logging.info('retrieve mgmtCmd result')

        return True, self.execStatus, self.execResult

    def createSubscription(self, node_id, subs_name, container_name, noti_client_id):
        if len(self.ukey) == 0:
            logging.warning('Invalid user key')
            return False

        if len(self.app_eui) == 0:
            logging.warning('Need to set APP EUI')
            return False

        header = {"Accept": "application/json",
                  "X-M2M-Origin": node_id,
                  "X-M2M-RI": node_id + "_" + str(random.randrange(1000, 1100)),
                  "X-M2M-NM": subs_name,
                  "Content-Type": "application/vnd.onem2m-res+xml;ty=23",
                  "uKey": self.ukey
                  }

        payload = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n" + \
                  "<m2m:sub \n" + \
                  "    xmlns:m2m=\"http://www.onem2m.org/xml/protocols\" \n" + \
                  "    xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">\n" + \
                  "    <enc>\n" + \
                  "         <rss>1</rss>\n" + \
                  "    </enc>\n" + \
                  "    <nu>MQTT|" + noti_client_id + "</nu>\n" + \
                  "    <nct>1</nct>\n" + \
                  "</m2m:sub>"
        # <nct>, 1 : Modified Attribute only, 2: Whole Resource

        # query = '/ThingPlug/v1_0/remoteCSE-' + node_id + '/container-' + container_name
        query = '/' + self.app_eui + '/v1_0/remoteCSE-' + node_id + '/container-' + container_name
        req_msg = {'method': 'POST', 'header': header, 'query': query, 'payload': payload}
        json_body = self.thingplugHttpReq(req_msg, 201)
        if json_body == False:
            return False

        logging.info('subscription is created')
        return True

    def retrieveSubscription(self, node_id, subs_name, container_name):
        if len(self.ukey) == 0:
            logging.warning('Invalid user key')
            return False

        if len(self.app_eui) == 0:
            logging.warning('Need to set APP EUI')
            return False

        header = {"Accept": "application/json",
                  "X-M2M-Origin": node_id,
                  "X-M2M-RI": node_id + "_" + str(random.randrange(1000, 1100)),
                  "uKey": self.ukey
                  }

        # query = '/ThingPlug/v1_0/remoteCSE-' + node_id + '/container-' + container_name + '/subscription-' + subs_name
        query = '/' + self.app_eui + '/v1_0/remoteCSE-' + node_id + '/container-' + container_name + '/subscription-' + subs_name
        req_msg = {'method': 'GET', 'header': header, 'query': query, 'payload': ''}
        json_body = self.thingplugHttpReq(req_msg, 200)
        if json_body == False:
            return False

        logging.info('registered subscription')
        return True

    def deleteSubscription(self, node_id, subs_name, container_name):
        if len(self.ukey) == 0:
            logging.warning('Invalid user key')
            return False

        if len(self.app_eui) == 0:
            logging.warning('Need to set APP EUI')
            return False

        header = {
            'accept': "application/json",
            'x-m2m-ri': node_id + "_" + str(random.randrange(1000, 1100)),
            'x-m2m-origin': node_id,
            'ukey': self.ukey,
            'content-type': "application/vnd.onem2m-res+xml;ty=23",
        }

        # query = "/ThingPlug/v1_0/remoteCSE-" + node_id + "/container-" + container_name + "/subscription-" + subs_name
        query = '/' + self.app_eui + '/v1_0/remoteCSE-' + node_id + '/container-' + container_name + '/subscription-' + subs_name
        req_msg = {'method': 'DELETE', 'header': header, 'query': query, 'payload': ''}
        json_body = self.thingplugHttpReq(req_msg, 200)
        if json_body == False:
            return False

        logging.info('subscription is deleted')
        return True

    def getUserId(self):
        return self.user_id

    def getUserPw(self):
        return self.user_pw

    def getuKey(self):
        return self.ukey

    def getDevList(self):
        return self.deviceList

    def mqttConnect(self):
        if self.mqttc != None:
            self.mqttc.reinitialise(self.mqtt_client_id)
        else:
            self.mqttc = mqtt.Client(self.mqtt_client_id)

        self.mqttc.on_connect = self.mqtt_on_connect
        self.mqttc.on_message = self.mqtt_on_message

        try:
            self.mqttc.username_pw_set(self.getUserId(), self.getuKey())
            self.mqttc.connect(self.host, 1883, 60)
        except:
            return

    def mqttSetOnMessage(self, on_message_cb):
        self.mqttc.on_message = on_message_cb

    def mqttSetOnConnect(self, on_connect_cb):
        self.mqttc.on_connect = on_connect_cb

    def mqttDisconnect(self):
        if self.mqttc == None:
            return False

        self.mqttc.disconnect()
        self.mqttc.loop_stop()

    def mqttLoopForever(self):
        self.mqttc.loop_forever()

    def mqttLoop(self):
        self.mqttc.loop_start()

    def mqtt_on_connect(self, mqttc, userdata, flags, rc):
        logging.info('mqtt connected')
        subs_topic = '/oneM2M/req_msg/+/' + self.mqtt_client_id
        self.mqttSubscribe(subs_topic)

    def mqtt_on_message(self, mqttc, userdata, msg):
        return

    def mqttSubscribe(self, topic):
        self.mqttc.subscribe(topic)

    def setMqttClientId(self, client_id):
        self.mqtt_client_id = client_id

    def setDataServerInfo(self, host, port):
        self.data_server_host = host
        self.data_server_port = port

    def setAppEui(self, app_eui):
        self.app_eui = app_eui

sys.path.insert(0,'../')
# from ThingPlugApi import ThingPlug_Py3 

THINGPLUG_HOST = 'thingplugpf.sktiot.com'
THINGPLUG_PORT = 9000

import time, datetime
from bs4 import BeautifulSoup

MQTT_CLIENT_ID = 'bridge'
SUBS_PREFIX = 'thingplug_'
CONTAINER = 'LoRa'

# WaterVal_ref = db.reference('WaterValue/ID')
# last_val_ref = WaterVal_ref.order_by_key().limit_to_last(1).get()
# last_val = list(last_val_ref.values())
# temp = last_val[0]
temp = 0
today_val = 0

def mqtt_on_message_cb(client, userdata, msg):
   global today_val   
   global temp
   # logging.info(msg.topic)
   # logging.info(msg.payload)   
   xml_root = BeautifulSoup(msg.payload,'html.parser')
   device_name = getattr(xml_root.find('fr'),'string', None)
   data_payload = getattr(xml_root.find('pc').find('cin').find('con'), 'string', None)
   lt_time = getattr(xml_root.find('pc').find('cin').find('lt'), 'string', None)

   current_time = str(datetime.datetime.now())
   output_data = current_time + ',' + device_name + ',' + data_payload + ',' + lt_time + '\r\n'
   print (output_data)
   
   #hex_sym_calculate & predict_water_val--------------------
   h1=calculate(9,data_payload)
   h2=calculate(10,data_payload)
   h3=calculate(11,data_payload)
   h4=calculate(12,data_payload)
   calculated_data = (h4*10000 + h3*100 + h2)+ h1*0.01
      
   if calculated_data != temp:
      current_val = calculated_data - temp
      today_val += current_val
      temp = calculated_data

      today = time.strftime('%Y-%m-%d', time.localtime(time.time()))
      ref = db.reference('WaterValue/ID') #ID를 독거노인 Uid로 수정해야 함
      ref.update({('{}').format(today):{
		'date':('{}').format(today),
		'value':'%s' %today_val}
		})
   #------------------------------------------------------

   if enable_log > 0:
      f = open('subscription_mqtt.log','a')
      f.write(output_data)
      f.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'ThingPlug Subscription(MQTT) Example')
    
    parser.add_argument('-u', '--user_id', type=str, help='ThingPlug User ID', required=True)
    parser.add_argument('-p', '--user_pw', type=str, help='ThingPlug User Password', required=True)
    parser.add_argument('-ae', '--app_eui', type=str, help='ThingPlug APP EUI', required=True)

    parser.add_argument('-ni', '--node_id', type=str, help='ThingPlug Node ID', required=False)
    parser.add_argument('-ct', '--container', type=str, help='ThingPlug Container Name(Default:LoRa)', required=False)
    parser.add_argument('-th', '--thingplug_host', type=str, help='ThingPlug Host IP(Default:onem2m.sktiot.com)', required=False)
    parser.add_argument('-tp', '--thingplug_port', type=int, help='ThingPlug Port(Default:9443)', required=False)
    parser.add_argument('-ci', '--mqtt_client_id', type=str, help='ThingPlug MQTT Client ID(Deafult:bridge)', required=False)
    parser.add_argument('-el', '--enable_log', type=int, help='', required=False)

    args = parser.parse_args()
    
    if args.container      != None:    CONTAINER = args.container
    if args.thingplug_host != None:    THINGPLUG_HOST = args.thingplug_host
    if args.thingplug_port != None:    THINGPLUG_PORT = args.thingplug_port
    if args.mqtt_client_id != None:    MQTT_CLIENT_ID = args.mqtt_client_id

    global enable_log
    enable_log = 0
    if args.enable_log     != None:    enable_log = 1
        
    
    thingplug = ThingPlug(THINGPLUG_HOST,THINGPLUG_PORT)
    thingplug.login(args.user_id, args.user_pw)
    
    thingplug.setAppEui(args.app_eui)
    thingplug.getDeviceList()

    mqtt_client_id = thingplug.getUserId() + '_' + MQTT_CLIENT_ID 
    thingplug.setMqttClientId(mqtt_client_id)
    thingplug.mqttConnect()
    thingplug.mqttSetOnMessage(mqtt_on_message_cb)
    

    if args.node_id == None:
        status,node_cnt,node_list = thingplug.getDeviceList()
    
        if node_cnt == None:
            logging.warning('Node list is empty')
            sys.exit()
    
        for i in range(int(node_cnt)):
            subs_name = SUBS_PREFIX + node_list[i]
            if thingplug.retrieveSubscription(node_list[i], subs_name, CONTAINER) == True:
                thingplug.deleteSubscription(node_list[i], subs_name, CONTAINER)
             
            thingplug.createSubscription(node_list[i], subs_name, CONTAINER, mqtt_client_id)
    else:
        subs_name = SUBS_PREFIX + args.node_id
        if thingplug.retrieveSubscription(args.node_id, subs_name, CONTAINER) == True:
            thingplug.deleteSubscription(args.node_id, subs_name, CONTAINER)
        
        thingplug.createSubscription(args.node_id, subs_name, CONTAINER, mqtt_client_id)
    
    thingplug.mqttLoopForever()
