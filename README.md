# PixivのフォローリストからPawooをフォローするやつ
## 準備
*モジュールのインストール  

```bash:Terminal
pip install pixivpy  
pip install beautifulsoup4  
pip install robobrowser  
pip install lxml  
pip install Mastodon.py  
```  

*pivivpyの認証情報の準備  

```json:client.json  
{  
	"pixiv_id": "自分のPixivID(文字列の方)",  
	"password": "自分のPixivパスワード",  
	"user_id": "自分のユーザーID(数値の方)"  
}  
```

*Mastodon.pyの登録　Pythonのコンソールから  

```python:Terminal  
>> from mastodon import Mastodon  
>> Mastodon.create_app("client name", api_base_url = "https://pawoo.net", to_file = "my_clientcred_pawoo.txt")  
>> mastodon = Mastodon(client_id="my_clientcred_pawoo.txt",api_base_url = "https://pawoo.net")  
>> mastodon.log_in("mail address", "passwd",to_file = "my_usercred_pawoo.txt")  
```  

## 参考
[pixivのフォローユーザーの漫画・イラストを一括DL - Qiita](https://qiita.com/Hirosaji/items/304de7508df4b1cae904)  
[mastodonをpythonからさわる API解説 - Qiita](https://qiita.com/code_monkey/items/e4929ef13e2a2032d467)
