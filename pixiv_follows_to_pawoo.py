#ここからhttps://qiita.com/Hirosaji/items/304de7508df4b1cae904のソースコード
#!/usr/bin/env PYTHONIOENCODING=UTF-8 python3
# -*- coding: utf-8 -*-

from pixivpy3 import *
import json
from time import sleep
import sys, io, re, os
from robobrowser import RoboBrowser
from bs4 import BeautifulSoup
import mastodon
import requests 

f = open("client.json", "r")
client_info = json.load(f)
f.close()

# pixivpyのログイン処理
api = PixivAPI()
aapi = AppPixivAPI()
aapi.login(client_info["pixiv_id"], client_info["password"])

# フォローユーザーの総数を取得
self_info = aapi.user_detail(client_info["user_id"])
following_users_num = self_info.profile.total_follow_users

# フォローユーザー一覧ページのページ数を取得
if(following_users_num%48 != 0):
    pages = (following_users_num//48)+1
else:
    pages = following_users_num//48

#タグ除去用
p = re.compile(r"<[^>]*?>")
# [jump:1]形式除去用
jump = re.compile(r"\[jump:.+\]")
#ファイルエンコード設定用
character_encoding = 'utf_8'

# Webスクレイパーのログイン処理
pixiv_url = 'https://www.pixiv.net'
browser = RoboBrowser(parser='lxml', history=True)
browser.open('https://accounts.pixiv.net/login')
form = browser.get_forms('form', class_='')[0]
form['pixiv_id'] = client_info["pixiv_id"]
form['password'] = client_info["password"]
browser.submit_form(form)

# フォローユーザー一覧ページのURLを設定
target_url = 'https://www.pixiv.net/bookmark.php?type=user&rest=show&p='

# 全てのフォローユーザーのユーザIDを取得
following_users_id = []
for i in range(1, pages+1):
    print(target_url + str(i))
    browser.open(target_url + str(i))
    following_users = browser.find(class_='members')
    for user in following_users.find_all("input"):
        following_users_id.append(user.get("value"))
    sleep(3) # ページを移動したら一時待機する（マナー）
#ここまで元ソースコピペ

#pawooにログイン
pawoo = mastodon.Mastodon(
	client_id = "my_clientcred_pawoo.txt",
	access_token = "my_usercred_pawoo.txt",
	api_base_url = "https://pawoo.net"
)

#Pawoo紐づけてるアカウントを抽出してフォロー
for i in range (0, following_users_num):
	json_result = aapi.user_detail(following_users_id[i])
	if (json_result.profile.pawoo_url != None):
		print(json_result.user.name)
		pawoo_url = requests.get(json_result.profile.pawoo_url)
		if(pawoo_url.status_code != 200):
			print("Not found userpage")
			continue
		pawoo_id = pawoo_url.url.lstrip("https://pawoo.net/") + "@pawoo.net"
		print(pawoo_id)
		try:
			pawoo_user_detail = pawoo.account_search(pawoo_id, limit=1)
		except Exception as e:
			print(e)
			continue

		pawoo_num_id = pawoo_user_detail[0]['id']
		try:
			follow_result = pawoo.account_follow(pawoo_num_id)
			if (follow_result.following == True):
				print("Following")
			elif (follow_result.requested == True):
				print("Send follow request")
		except Exception as e:
			print(e)

	sleep(3)
