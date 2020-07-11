import requests
import json
import datetime
import time
import os

BLOCK_IDS = ['r-wakatsuki', 'shiracamus', 'PYTHONISTA', 'DaikiSuyama']

def lambda_handler(event, content):
    token = os.environ['QIITA_API_KEY']
    body_text = make_body(token)
    result = patch_article(body_text, token)
    return result


def get_last_day_posts(target_date, token):
    before_date = target_date - datetime.timedelta(days=2)

    headers = {'Authorization': 'Bearer {}'.format(token)}
    url_target_date = 'https://qiita.com/api/v2/items?page=1&per_page=100&query=tag%3APython+created%3A' + \
        target_date.strftime("%Y-%m-%d")
    url_before_date = 'https://qiita.com/api/v2/items?page=1&per_page=100&query=tag%3APython+created%3A' + \
        before_date.strftime("%Y-%m-%d")

    last_day_post = []
    for url in [url_target_date, url_before_date]:
        response = requests.get(url, headers=headers)
        data = json.loads(response.text)
        for d in data:
            created_at = datetime.datetime.strptime(
                d['created_at'], '%Y-%m-%dT%H:%M:%S+09:00')
            if created_at.strftime("%Y-%m-%d") == target_date.strftime("%Y-%m-%d"):
                last_day_post.append(d)
    return last_day_post


def get_backnumber(target_date, token):
    headers = {'Authorization': 'Bearer {}'.format(token)}
    url_back = 'https://qiita.com/api/v2/items?page=1&per_page=100&query=tag%3APython+created%3A%3C' + \
        target_date.strftime("%Y-%m-%d")
    response = requests.get(url_back, headers=headers)
    data = json.loads(response.text)
    backnumber = []
    for d in data:
        created_at = datetime.datetime.strptime(
            d['created_at'], '%Y-%m-%dT%H:%M:%S+09:00')
        if created_at.strftime("%Y-%m-%d") != target_date.strftime("%Y-%m-%d"):
            if d['likes_count'] > 2:
                backnumber.append(d)
    return backnumber


def make_body(token):
    jst = datetime.datetime.utcfromtimestamp(
        time.time()) + datetime.timedelta(hours=9)
    last_day = jst - datetime.timedelta(days=1)
    last_day_post = get_last_day_posts(last_day, token)
    last_day_post = sorted(
        last_day_post, key=lambda x: x['likes_count'], reverse=True)

    backnumber = get_backnumber(last_day, token)
    backnumber = sorted(
        backnumber, key=lambda x: x['likes_count'], reverse=True)

    body_text = "このページは毎日自動更新され、前日に投稿されたPython関連の記事一覧を表示します\n"
    body_text += "（掲載を希望されない場合はコメントなどで反応してくだされば、掲載しないように対応いたします(6/26:コメントをくださった記事は除外するように実装しました)）\n"
    body_text += f"最終更新: {jst.month}月{jst.day}日{jst.strftime('%-H時%M分')}\n"
    body_text += "# {}年{}月{}日に投稿された記事\n".format(last_day.year, last_day.month, last_day.day)
    for article in last_day_post:
        if article['user']['id'] not in BLOCK_IDS:
            created_at = datetime.datetime.strptime(
                article['created_at'], '%Y-%m-%dT%H:%M:%S+09:00')
            body_text += '##### ' + '[' + str(article['likes_count']) + '👍]' + '[' + article['title'] + \
                '](' + article['url'] + ')' + '(' + \
                created_at.strftime('%-H時%M分') + '投稿)' + '\n'

    body_text += "# いいねが多い最近の記事\n"
    for article in backnumber:
        if article['user']['id'] not in BLOCK_IDS:
            created_at = datetime.datetime.strptime(
                article['created_at'], '%Y-%m-%dT%H:%M:%S+09:00')
            body_text += '##### ' + '[' + str(article['likes_count']) + '👍]' + '[' + article['title'] + \
                '](' + article['url'] + ')' + '(' + \
                created_at.strftime('%Y年%-m月%-d日') + '投稿)' + '\n'

    return body_text


def patch_article(body_text, token):
    body_json = {
        "body": body_text,
        "coediting": False,
        "private": False,
        "tags": [
            {
                "name": "Python"
            }
        ],
        "title": "Python記事まとめ(毎日自動更新)",
    }

    url_items = 'https://qiita.com/api/v2/items'
    item_id = "eaf1d7b945b3a61a4fdd"
    headers = {'Authorization': 'Bearer {}'.format(token)}
    response = requests.patch(
        url_items + '/' + item_id, headers=headers, json=body_json)
    return response.status_code