from flask import Flask, render_template
from flask import Flask
from markupsafe import escape
from konlpy.tag import Okt

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

import json

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

app = Flask (__name__)
@app.route('/<target>')

def test(target):
   ref = db.reference('EmotionalAnalysis/{}').format(target)
   record = ref.child('record').get()


   ksl = KnuSL
   testlist = twitter.morphs(record)
   total_score = 0

   for j in range(0, len(testlist)):
      wordname = testlist[j]
      if ksl.data_list(wordname) != 'None':
         total_score += int(ksl.data_list(wordname))
         #print(wordname)

   #print(total_score)

   return total_score


if __name__ == "__main__":
    app.run(host="0.0.0.0", port="5000")
