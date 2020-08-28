import subprocess
import json
import requests
import time
from pydict import Dict
import jieba
from utils import *
from duckling import *
import threading
from flask import Flask, request, Response

import argparse

import sys
import os.path
module_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(module_dir + '/data/textsmart/lib/')
from tencent_ai_texsmart import *

app = Flask(__name__)

parser = argparse.ArgumentParser()
parser.add_argument('--p', type=int, default=6787)
parser.add_argument('--duck', type=int, default=6788)
args = parser.parse_args()

addr = Dict("data/regions")
music = Dict("data/music")
engine = NluEngine(module_dir + '/data/textsmart/data/nlu/kb/', 1)
subprocess.Popen(['./data/duckling', f'--port={args.duck}'])
ling = Duckling(url=f'http://127.0.0.1:{args.duck}/parse')

class decode_thread(threading.Thread):
    def __init__(self, task, text):
        threading.Thread.__init__(self)
        self.task = task
        self.text = text
        self.res = []

    def run(self):
        if self.task == 'general':
            self.res = process_general(self.text, ling)
        elif self.task == 'addr':
            self.res = process_addr(process_match_res(self.text, addr), self.text)
        elif self.task == 'music':
            self.res = process_music(self.text, music)
        elif self.task == 'ner':
            self.res = process_smart(engine.parse_text(self.text))

@app.route('/api')
def get():
    text = request.args.get('text', '')
    names = locals()
    threads = []
    for task in ['general', 'addr', 'ner', 'music']:
        names['tagger%s' % task] = decode_thread(task, text)
        threads.append(names['tagger%s' % task])
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    result = []
    for thread in threads:
        result.extend(thread.res)
    post_process(result)
    return Response(json.dumps(result, ensure_ascii=False), mimetype='application/json; charset=utf-8')

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=args.p,threaded=True)
