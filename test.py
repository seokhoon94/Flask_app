from flask import Flask, render_template
from flask import Flask


app = Flask (__name__)
 
@app.route('/')
def main():
    f = open("C:\\Users\\hsh96\\Desktop\\FlaskApp\\hi.txt", 'r')
    data = f.read()
    f.close() 
    return data  

if __name__ == "__main__":
    app.run(host="0.0.0.0", port="5000")
