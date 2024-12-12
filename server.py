import logging
import json
import requests

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from multiprocessing import Process
from typing import ChainMap
from urllib.parse import ParseResult, parse_qs, urlparse

def requests_get(url):
    try:
        requests.get(url)
    except Exception as e:
        pass

def login(parse: ParseResult):
    query = parse_qs(parse.query)
    username = query.get('username', [''])[0]
    password = query.get('password', [''])[0]
    if 'admin' == username and 0 < len(password):
        return {'code': 20000, 'data': {'token': 'admin-token'}}
    else:
        return {'code': 60204, 'message': 'Account and password are incorrect.'}

def info(parse: ParseResult):
    query = parse_qs(parse.query)
    token = query.get('token', [''])[0]
    if 'admin-token' == token:
        return {'code': 20000, 'data': {
            'roles': ['admin'],
            'introduction': 'I am a super administrator',
            'avatar': 'https://wpimg.wallstcn.com/f778738c-e4f8-4870-b634-56703b4acafe.gif',
            'name': 'Super Admin'
        }}
    else:
        return {'code': 50008, 'message': 'Login failed, unable to get user details.'}

def stategy():
    url = 'http://localhost:8123/index'
    IxHandler.state
    try:
        data1 = requests.get(url, timeout=1)
        if 200 == data1.status_code:
            return {'code': 20000, 'info': dict(ChainMap(IxHandler.state, json.loads(data1.text)))}
    except Exception as e:
        pass
    return {'code': 90001, 'message': 'stategy error'}

def setting(parse: ParseResult):
    query   = parse_qs(parse.query)
    buy     = query.get('buy'   , [''])[0]
    short   = query.get('short' , [''])[0]
    chan    = query.get('chan'  , [''])[0]
    skdj    = query.get('skdj'  , [''])[0]
    worth   = query.get('worth' , [''])[0]
    IxHandler.state['buy']      = True if buy!='0' else False
    IxHandler.state['short']    = True if short!='0' else False
    IxHandler.state['chan']     = True if chan!='0' else False
    IxHandler.state['skdj']     = True if skdj!='0' else False
    IxHandler.state['worth']    = True if worth!='0' else False
    with open('config.json', 'r') as f:
        config = json.load(f)
        config['state'] = IxHandler.state
        with open('config.json','w',encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False)
            return {'code': 20000, 'message': 'config saved'}
        
def vnpy(parse: ParseResult):
    query = parse_qs(parse.query)
    flag = query.get('flag', [''])[0]
    sign = query.get('sign', [''])[0]
    key = query.get('key', [''])[0]
    stamp = query.get('stamp', [''])[0]
    if '1' == flag[:1] and len(flag) == 4 and IxHandler.state['chan']:
        print('chan is blocking')
        return
    if '2' == flag[:1] and len(flag) == 4 and IxHandler.state['skdj']:
        print('skdj is blocking')
        return
    if '1' == key and IxHandler.state['buy']:
        print('buy is blocking')
        return
    if '2' == key and IxHandler.state['short']:
        print('short is blocking')
        return 
    if 3 <= int(key) and IxHandler.state['worth']:
        mark = '1'
    else:
        mark = '0'
    url = 'http://localhost:8123/vnpy?flag=%s&sign=%s&mark=%s&key=%s&stamp=%s' % (flag, sign, mark, key, stamp)
    request = Process(target=requests_get, args=(url,))
    request.start()
    return {'flag': flag, 'sign': sign, 'key': key, 'stamp': stamp}

def forward(parse: ParseResult):
    url='http://localhost:8123%s?%s' % (parse.path, parse.query)
    print('=====%s=====' % url)
    request = Process(target=requests_get, args=(url,))
    request.start()
    return {'path': parse.path, 'query': parse.query}

class IxHandler(BaseHTTPRequestHandler):
    state = {}
    config = {}
    def ixResponse(self, response):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response_json = json.dumps(response)
        self.wfile.write(response_json.encode('utf-8'))

    def ixSaved(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        data = json.loads(body.decode('utf-8'))
        if data.get('action') == 'config':
            IxHandler.config = data.get('content')
            with open('config.json', 'r') as f:
                config = json.load(f)
                config['setting'] = IxHandler.config
                with open('config.json','w',encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False)
            return {'code': 20000, 'data': 'ok'}
        return {'code': 90002, 'message': 'saved error'}
            
    def log_message(self, format, *args):
        if self.path[:7] == '/config':
            return
        BaseHTTPRequestHandler.log_message(self, format, *args)
        pass

    def do_GET(self):
        parse = urlparse(self.path)
        if parse.path == '/favicon.ico':
            response = {'code': 40404, 'message': 'no ico'}
        elif parse.path == '/login':
            response = login(parse)
        elif parse.path == '/logout':
            response = {'code': 20000, 'data': 'success'}
        elif parse.path == '/info':
            response = info(parse)
        elif parse.path == '/load':
            self.server.ixLoad()
            response = {'code': 20000, 'message': 'loaded new config'}
        elif parse.path == '/stategy':
            response = stategy()
        elif parse.path == '/config':
            response = {'code': 20000, 'data': IxHandler.config}
        elif parse.path == '/setting':
            response = setting(parse)
        elif parse.path == '/vnpy':
            response = vnpy(parse)
        else:
            response = forward(parse)
        self.ixResponse(response)
    def do_POST(self):
        self.ixSaved()

class IxServer(ThreadingHTTPServer):
    def __init__(self):
        self.timeout = 1
        super().__init__(('0.0.0.0', 8989), IxHandler)
        self.ixLoad()
    def ixLoad(self):
        with open('config.json', 'r') as f:
            config = json.load(f)
            IxHandler.state = config['state']
            IxHandler.config = config['setting']

if __name__ == '__main__':
    logging.getLogger("requests").setLevel(logging.DEBUG)
    server = IxServer()
    print('Starting server')
    server.serve_forever()
