from flask import Flask, render_template
from flask import Flask
from markupsafe import escape


app = Flask (__name__)

 
@app.route('/')
def test():
    return 'test'
    

if __name__ == "__main__":
    app.run()