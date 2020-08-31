import jieba 
import jieba.posseg as pseg
import json
import re

regex = {
    'id_number': '^[1-9]\d{7}((0\d)|(1[0-2]))(([0|1|2]\d)|3[0-1])\d{3}$|^[1-9]\d{5}[1-9]\d{3}((0\d)|(1[0-2]))(([0|1|2]\d)|3[0-1])\d{3}([0-9]|X)$',
    'passport': '^[E|G]\d{8}$'
}
def process_match_res(text, d):
    dres = d.multi_match(text)
    res = []
    for k in dres:
        tmp = {}
        tmp['text'] = k
        tmp['start'] = dres[k]['hits'][0]['start']
        tmp['end'] = dres[k]['hits'][0]['end']
        tmp['type'] = list(dres[k]['value'].keys())[0]
        tmp['properties'] = dres[k]['value'][tmp['type']]['type']
        res.append(tmp)
    return res

def process_regex(text):
    res = []
    for k in regex:
        r = re.finditer(regex[k], text)
        for e in r:
            tmp = {}
            tmp['text'] = e.group(0)
            tmp['start'] = e.start()
            tmp['end'] = e.end()
            tmp['type'] = k
            tmp['properties'] = ''
            res.append(tmp)
    return res

def process_music(text, d):
    dres = d.multi_max_match(text)
    pos = []
    for word, flag in pseg.cut(text):
        pos += [flag] * len(word)
    for k,v in list(dres.items()):
        token_pos = list(set(pos[v['hits'][0]['start']:v['hits'][0]['end']]))
        if len(token_pos) == 1 and token_pos[0].startswith(('u', 'm')):
            del dres[k]
    res = []
    for k in dres:
        tmp = {}
        tmp['text'] = k
        tmp['start'] = dres[k]['hits'][0]['start']
        tmp['end'] = dres[k]['hits'][0]['end']
        tmp['type'] = [l for l in list(dres[k]['value'].keys()) if l != 'potential_type'][0]
        tmp['properties'] = dres[k]['value'][tmp['type']]
        if 'potential_type' in dres[k]['value']:
            tmp['properties']['potential_type'] = dres[k]['value']['potential_type']
        res.append(tmp)

    return res


def process_addr(res, query):
    tokenized = list(jieba.tokenize(query))
    boundaries = {k[1]:k[2] for k in tokenized if k[2] > k[1] + 1}
    for i in range(len(res) - 1, -1, -1):
        if res[i]['start'] not in boundaries:
            del res[i]
        elif len(res[i]['text']) <= 1:
            del res[i]
        elif res[i]['properties'][0][0] == 'village' and len(res[i]['text']) == 2:
            del res[i]
    for i in range(len(res)):
        res[i]['type'] = res[i]['properties'][0][0]
        if len(res[i]['properties']) > 1:
            res[i]['properties'] = {
                'code': res[i]['properties'][0][1],
                'potential_type': res[i]['properties'][1][0],
                'potential_code': res[i]['properties'][1][1]
                }
        else:
            res[i]['properties'] = {
                'code': res[i]['properties'][0][1]
            }
    return res

def process_smart(output):
    res = []
    for entity in output.entities():
        properties = {}
        if entity.type.name.startswith(('loc.admin', 'time', 'number', 'quantity')):
            continue
        if entity.type.name.startswith(('basic')):
            print(entity.type.name)
        tmp = {
            'text': entity.str, 
            'start': entity.offset, 
            'end': entity.offset + entity.len, 
            'type': entity.type.name.split('.')[0]}
        try:
            properties = json.loads(entity.meaning)
        except:
            tmp['properties'] = ""
        if 'related' in properties:
            tmp['properties'] = properties['related'][:3]
        elif 'value' in properties:
            tmp['properties'] = properties['value']
        res.append(tmp)
    return res

def process_general(text, ling):
    res = []
    output = ling(text)
    for e in output:
        res.append({
                'text': e['body'],
                'start': e['start'],
                'end': e['end'],
                'type': e['dim'],
                'properties': e['value']})
    tokenized = list(jieba.tokenize(text))
    boundaries = {k[1]:k[2] for k in tokenized if k[2] > k[1] + 1}
    for i in range(len(res) - 1, -1, -1):
        if res[i]['start'] not in boundaries:
            del res[i]
    return res

def post_process(result):
    result.sort(key=lambda k: (int(k.get('start', 0))))
    result = [e for e in result if len(e['text']) > 1]
