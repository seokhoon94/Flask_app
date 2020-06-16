from flask import Flask, render_template
from flask import Flask
from markupsafe import escape

from konlpy.tag import Okt
twitter = Okt()

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

import json

import time, datetime

app = Flask (__name__)

db_url = 'https://firstproject-afb38.firebaseio.com/'
cred = credentials.Certificate("firstproject-afb38-firebase-adminsdk-r6fpm-9c4723acd5.json")
default_app = firebase_admin.initialize_app(cred, {'databaseURL':db_url})

#send_message--------------------------------------
from pyfcm import FCMNotification
import schedule
from apscheduler.schedulers.background import BackgroundScheduler 
from apscheduler.jobstores.base import JobLookupError

push_service = FCMNotification(api_key='AAAAkyLbc_g:APA91bHbxHV_Xfl8-CaFCFNQy_dD_s9PO5aikbG89JZ8gpi0T8Oga8saiu0d1GaicZwhWF53akjBxfjhKH016aNDhGNUV2dc6ZNwau7kDJherVqaK_hEjb0hOgkSMSsvQTdKqkYC7iwc')

def send_message(token, name):
	
  result = push_service.notify_single_device(registration_id=token,
                                             message_title='위험 경고',
                                             message_body=name+' 독거노인의 위험이 의심됩니다. 자택에 방문해 주세요')

def error_check(UID):
  today = datetime.date.today()
  yesterday = today - datetime.timedelta(days=1)

  ref = db.reference(('Group/{}/Risk').format(UID))
  risk = float(ref.get())

  ref =  db.reference('WaterValue/ID2')
  today_value = ref.child(('{}/value').format(yesterday)).get()
  today_predict =  ref.child(('{}/predict').format(yesterday)).get()

  error = abs((float(today_value) - float(today_predict))/float(today_value)*100)

  ref = db.reference(('Group/{}').format(UID))
  guardian_token = ref.child('guardian_token').get()
  token_list= []
  
  user_name = ref.child('oldman').get()

  for x in range(1,4):
      if ref.child(('manager{}_token').format(x)).get() != "null":
          token_list.append(ref.child(('manager{}_token').format(x)).get())
  if guardian_token != "null":
       token_list.append(ref.child('guardian_token').get())

  if risk <= -8:
     if error >= 3:
         for x in range(len(token_list)):
             send_message(token_list[x], user_name)
  elif (-7 <= risk <= 7):
       if error >= 5:
         for x in range(len(token_list)):
             send_message(token_list[x], user_name)
  elif  risk >= 8:
       if error >= 10:
         for x in range(len(token_list)):
             send_message(token_list[x], user_name)


twitter = Okt()

class KnuSL():

   def data_list(wordname):   
      with open('data/SentiWord_info.json', encoding='utf-8-sig', mode='r') as f:
         data = json.load(f)
      result = ['None','None']   
      for i in range(0, len(data)):
         if data[i]['word'] == wordname:
            result.pop()
            result.pop()
            result.append(data[i]['word_root'])
            result.append(data[i]['polarity'])   
      
      r_word = result[0]
      s_word = result[1]
                     
      # print('어근 : ' + r_word)
      # print('극성 : ' + s_word)      
      
      
      return s_word


@app.route('/<target>')
def test(target):
    ref = db.reference(('DailyRecord/{}').format(target))
    ref2 = db.reference(('Group/{}').format(target))
    if len(ref.get()) < 4:
        GroupN_date = ref.order_by_key().get()
    else:
        GroupN_date = ref.order_by_key().limit_to_last(4).get()



    if 'risk1' in ref2.get():
        for i in range(1,5,1):
            ref2.child('risk'+str(i)).set({'date' : "",'value' : 0})


    ksl = KnuSL
    def morphs(word): # record 계산법
        morphemes_of_record = twitter.morphs(word)
        record_score = 0  # record 점수 계산
        for j in range(0, len(morphemes_of_record)):
                    wordname = morphemes_of_record[j]
                    if ksl.data_list(wordname) != 'None':
                        record_score += int(ksl.data_list(wordname))
        return record_score

    meal_score = 0  # meal 점수 계산
    medicine_score = 0  # medicine 점수 계산
    condition_score = 0
    record__score=0
    count=0

    for key, val in GroupN_date.items():
        date = key
        count=count+1
        for key, val in val.items():
                for i in range(1, 4):
                    if key == 'meal' + str(i):
                        if val != "":
                            meal_score += 1
                    if key == 'medicine' + str(i) + 'check':
                        if val != "false":
                            medicine_score += 1
                if key == 'condition':
                    condition_score = val  # condition 점수 계산
                if key == 'record':
                    record2 = val
                    record__score = morphs(record2)
        total_score = record__score + meal_score + medicine_score + int(condition_score)
        ref2.child('risk' + str(count)).update({'date': date[4:8],
                                               'value': total_score})
    ref2.child('RiskDate').set(date[4:8])
    ref2.child('Risk').set(total_score)




@app.route('/mes/<UID>')
def safetycheck_send_message(UID):

  print('run')
  sched = BackgroundScheduler()
  sched.start()
  sched.add_job(error_check, 'cron', second='1', id="test_11", args=[UID])

  return 'return success'



@app.route('/servercheck')
def check():
   return 'server is running'
   

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
    # app.run()
