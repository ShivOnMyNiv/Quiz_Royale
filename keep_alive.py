# -*- coding: utf-8 -*-
"""
Created on Thu Nov 11 16:06:31 2021

@author: derph
"""

from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def main():
    return "I like pooping"

def run():
    app.run(host="0.0.0.0", port=8080)
    
def keep_alive():
    server = Thread(target=run)
    server.start()