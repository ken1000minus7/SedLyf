from flask import Flask
# from replit.web import App
from threading import Thread

app = Flask('')
# app = App('')

@app.route('/')
def home():
    return "Hello, I am alive!"

def run():
  app.run(host='0.0.0.0',port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()