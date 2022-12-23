# Pixiv follows to Pawoo follows

This script lets you automatically follow every one of your Pixiv follows'
Pawoo accounts. While this was not tested with other instances, it probably
will work even if your home instance is not on pawoo.net.

## Setup

First, install your pip dependencies. I highly recommend setting up a
pyenv-virtualenv for this. Google it if you don't know what that means.

```bash:Terminal
pip install pixivpy3
pip install Mastodon.py  
```  

Then, create your Mastodon credentials. The below example assumes your home
instance is on Pawoo as well, but I'm pretty sure it would only take minor
tweaks to make this work on other instances.

```python:Terminal  
>> from mastodon import Mastodon
>> instance = "https://pawoo.net"
>> Mastodon.create_app("pixiv_follows_to_pawoo", api_base_url=instance, to_file="mastodon_client_id.txt")
>> mastodon = Mastodon(client_id="mastodon_client_id.txt",api_base_url=instance)
>> mastodon.log_in("YOUR EMAIL HERE", "YOUR PASSWORD HERE", to_file="mastodon_access_token.txt")
```  

## Usage

Just run [`pixiv_follows_to_pawoo.py`](pixiv_follows_to_pawoo.py) as a script.
It will automatically open a browser for you to get your access code for pixiv
(since they disabled user/pass login with their API, like all modern APIs do,
because we live in hell.) Instructions on what to do when it opens the browser
are in [`pixiv_auth.py`](pixiv_auth.py), which is its own script which came
from a [well-known
gist](https://gist.github.com/ZipFile/c9ebedb224406f4f11845ab700124362), but
I modified it so that you don't have to run it on its own, nor copy-paste
creds from the terminal. But you do still have to get the code from the
network console. I summarized the instructions in the script itself, just in
case that gist link dies.

Warning: Pawoo has rate limits, but the Mastodon client tries to work around
them. YMMV. More info
[here](https://mastodonpy.readthedocs.io/en/stable/01_general.html#rate-limiting).

I should also say, I found pixivpy to be unreliable and to return garbage data
from time to time. Furthermore, the method that `pixiv_auth.py` uses to get
a refresh token doesn't work all the time, and I can't figure out why. Sorry.
I blame OAuth and other such degenerate web 2.0 bullshit.

## Original blog post from the original author (in Japanese)

I can't read this at all, so I had to figure everything out manually, but
if you want to look at the original author's posts, here they are:

* [pixivのフォローユーザーの漫画・イラストを一括DL - Qiita](https://qiita.com/Hirosaji/items/304de7508df4b1cae904)
* [mastodonをpythonからさわる API解説 - Qiita](https://qiita.com/code_monkey/items/e4929ef13e2a2032d467)

## License

The original author did not license their code, so technically all rights are
reserved by them, but they haven't updated it since their first commit and they
probably don't even speak English, so I doubt they would sue either you or I
for using or distributing this extremely modified version.

As far as I'm concerned, if my own contributions can be licensed, they are
licensed under the [CNPL-NAv7+](https://thufie.lain.haus/NPL.html).
