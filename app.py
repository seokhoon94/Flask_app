from flask import Flask, render_template
from flask import Flask

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

db_url = 'https://firstproject-afb38.firebaseio.com/'

cred = credentials.Certificate("firstproject-afb38-firebase-adminsdk-r6fpm-9c4723acd5.json")

default_app = firebase_admin.initialize_app(cred, {'databaseURL':db_url})

ref = db.reference('Users')
row = ref.get()

 
app = Flask (__name__)
 
@app.route('3.16.114.166')
 "test"
 
@app.route('3.16.114.166'/i)
def colon(row)
  return row
def main():
   
    retern 0
 

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)


