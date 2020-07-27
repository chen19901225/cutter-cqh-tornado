from tornado import simple_httpclient
import json


async def util_mattermost_send_text(url, server_name, content, logger):
    if not url:
        logger.warning("mattermost_url is empty")
        return
    d = {"text": "server_name:{}\n{}\ncontent:{},{}".format(
        server_name,
        '='.center(80, '='),
        content,
        '='.center(80, '='),
    )}
    body = json.dumps(d, ensure_ascii=False)
    httpclient = simple_httpclient.AsyncHTTPClient()
    res = await httpclient.fetch(url, method="POST", headers={"Content-Type": "application/jsohn"},
                                 body=body)
    if res.code != 200:
        logger.error("fail to send mattermost {}".format(url))
