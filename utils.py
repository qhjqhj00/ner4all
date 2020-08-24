import jieba 

def process_match_res(text, d):
    dres = d.multi_match(text)
    res = []
    for k in dres:
        tmp = {}
        tmp['text'] = k
        tmp['start'] = dres[k]['hits'][0]['start']
        tmp['end'] = dres[k]['hits'][0]['end']
        tmp['type'] = list(dres[k]['value'].keys())[0]
        tmp['properties'] = dres[k]['value'][tmp['type']]
        res.append(tmp)
    return res


def process_addr(res, query):
    tokenized = list(jieba.tokenize(query))
    boundaries = {k[1]:k[2] for k in tokenized if k[2] > k[1] + 1}
    res = [k for k in res if k['start'] in boundaries and len(k['text']) > 1]
    return res