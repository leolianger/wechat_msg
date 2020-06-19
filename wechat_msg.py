import flask
import markdown
import uuid
import os
import redis
import requests
import time
import re
import json5
with open('cfg.json','r') as f:
    cfg=json5.load(f)

pool=redis.ConnectionPool(host=cfg['redis_ip'],port=cfg['redis_port'],password=cfg['redis_pass'])
redisClient=redis.StrictRedis(connection_pool=pool)
#30天
expire_ms=1000*60*60*24*30
app=flask.Flask(__name__)
root_path=os.path.realpath(os.path.split(__file__)[0])

def md2html(md_content):
    exts=['markdown.extensions.extra','markdown.extensions.codehilite','markdown.extensions.tables',
          'markdown.extensions.toc']
    html=markdown.markdown(md_content,extensions=exts)
    content = flask.Markup(html)
    return content

@app.route('/view/<id>',methods=['GET'])
def view(id):
    mark=redisClient.get(f'{cfg["redis_tag"]}{id}')
    if mark:
        content=md2html(mark.decode('utf-8'))
        html=flask.render_template('index.html',**locals())
        return html
    return None

# @app.route('/save/<mark>',methods=['post','get'])
def save(mark):
    while True:
        id=uuid.uuid4().hex
        has=redisClient.get(f'{cfg["redis_tag"]}{id}')
        if not has:
            break
    redisClient.set(f'{cfg["redis_tag"]}{id}',str(mark).encode('utf-8'))
    redisClient.expire(f'{cfg["redis_tag"]}{id}',expire_ms)
    return id

def digest_mark(mark):
    # 去掉markdown标签
    pattern = '[\\\`\*\_\[\]\#\+\-\!\>]'
    content = re.sub(pattern, '', mark)
    #取前150字符作为文章摘要
    return content#[:155]

def get_url(title,content):
    mark = f'###{title}\n----\n{content}'
    id = save(mark)
    url = f"{cfg['base_url']}view/{id}"
    return url

@app.route('/send',methods=['post','get'])
def send():
    args=flask.request.args
    app_id=args.get('sendkey')
    title=args.get('text')
    content=args.get('desp')
    if not content: content=''

    secret = cfg['agents'].get(app_id)
    if not secret:
        return 'sendkey is invaliad, please contact with admin to check sendkey'
    #获取access_token
    token_url="https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=%s&corpsecret=%s"%(cfg['corp_id'],secret)
    print(token_url)
    result=requests.get(token_url)
    dict_result=result.json()
    print(dict_result)
    access_token=dict_result['access_token']

    #生成通过post请求发送消息的url
    post_url="https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=%s"%(access_token)
    post_data={
        "touser":"@all",
        "agentid":app_id,
        "msgtype":"textcard",
        "textcard":{
            "title" : title,
            "description" : f"<div>{time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))}</div>{digest_mark(content)}",
            "url" : get_url(title,content),
            "btntxt":"详情"
        },
    }
    data = json5.dumps(post_data,quote_keys=True)
    headers = {'content-type':'application/json','charset':'utf-8'}
    result = requests.post(post_url,data=data,headers=headers)
    return result.text,result.status_code,result.headers.items()

if __name__=='__main__':
    app.debug=True
    app.run(host='0.0.0.0',port=8888)
