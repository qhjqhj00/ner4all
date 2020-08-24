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
args = parser.parse_args()

addr = Dict("data/regions")
ling = Duckling()
engine = NluEngine(module_dir + '/data/textsmart/data/nlu/kb/', 1)
subprocess.Popen('./data/duckling')

class decode_thread(threading.Thread):
    def __init__(self, task, text):
        threading.Thread.__init__(self)
        self.task = task
        self.text = text
        self.res = []

    def run(self):
        # now = time.time()
        if self.task == 'general':
            output = ling(self.text)
            for e in output:
                self.res.append(
                    {
                        'text': e['body'],
                        'start': e['start'],
                        'end': e['end'],
                        'type': e['dim'],
                        'value': e['value']
                    }
                )
        elif self.task == 'addr':
            self.res = process_addr(process_match_res(self.text, addr), self.text)
        elif self.task == 'ner':
            output = engine.parse_text(self.text)
            for entity in output.entities():
                tmp = {'entity': entity.str, 'start': entity.offset, 'length': entity.len, 'type': entity.type.name}
                try:
                    tmp.update(json.loads(entity.meaning))
                except:
                    tmp['value'] = ""
                self.res.append(tmp)
        # end = time.time()
        # print(f'{self.task}: {end-now}')

@app.route('/api')
def get():
    text = request.args.get('text', '')
    names = locals()
    threads = []
    for task in ['general', 'addr', 'ner']:
        names['tagger%s' % task] = decode_thread(task, text)
        threads.append(names['tagger%s' % task])

    result = []

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    for thread in threads:
        result.append(thread.res)

    return Response(json.dumps(result, ensure_ascii=False), mimetype='application/json; charset=utf-8')

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=args.p,threaded=True)
