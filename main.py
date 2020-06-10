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
    GroupN_date = ref.order_by_key().limit_to_last(4).get()
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
    count=1

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
        ref = db.reference(('Group/{}').format(target))
        ref.child('risk' + str(count)).update({'date': date[4:8],
                                               'value': total_score})


@app.route('/servercheck')
def check():
   return 'server is running'
   

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
    # app.run()
