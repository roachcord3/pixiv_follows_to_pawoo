#!/usr/bin/env python3
#
# original source: https://gist.github.com/ZipFile/c9ebedb224406f4f11845ab700124362
#
# the original wasn't licensed, but the original creator is not going after
# people who are forking and modifying the original gist (e.g. to make it
# use selenium), so while technically they reserve all rights, i bet they
# won't mind me copying this. this was last edited in 2022
#
# anyway, if the original url is dead, here is a tl;dr of their readme, so
# you can bootstrap your token:
#
# 1. run `python pixiv_auth.py login`, this opens a managed browser window
#    at the pixiv login page. (i edited the other file to do this part for
#    you automatically, but you can do this up front, by itself, if you want)
# 2. open dev console, networking pane
# 3. turn on persistent logging
# 4. filter for `callback?`
# 5. actually perform the login
# 6. copy the value of the `code` param from the logged request, paste it
#    into this script's prompt
#
# as far as im concerned, if my own contributions can be licensed, they are
# licensed under the CNPL-NAv7+. but all i did was separate the printing from
# the actual data fetching in the login and refresh methods, and type this,
# so, make of that what you will

from argparse import ArgumentParser
from base64 import urlsafe_b64encode
from hashlib import sha256
from pprint import pprint
from secrets import token_urlsafe
from sys import exit
from urllib.parse import urlencode
from webbrowser import open_new as open_url

import requests

# Latest app version can be found using GET /v1/application-info/android
USER_AGENT = "PixivAndroidApp/6.2.0 (Android 12; Pixel 7)"
REDIRECT_URI = "https://app-api.pixiv.net/web/v1/users/auth/pixiv/callback"
LOGIN_URL = "https://app-api.pixiv.net/web/v1/login"
AUTH_TOKEN_URL = "https://oauth.secure.pixiv.net/auth/token"
CLIENT_ID = "MOBrBDS8blbauoSck0ZfDbtuzpyT"
CLIENT_SECRET = "lsACyCD94FhDUtGTXi3QzcFE2uU1hqtDaKeqrdwj"


def s256(data):
    """S256 transformation method."""

    return urlsafe_b64encode(sha256(data).digest()).rstrip(b"=").decode("ascii")


def oauth_pkce(transform):
    """Proof Key for Code Exchange by OAuth Public Clients (RFC7636)."""

    code_verifier = token_urlsafe(32)
    code_challenge = transform(code_verifier.encode("ascii"))

    return code_verifier, code_challenge


def print_auth_token_response(response):
    data = response.json()

    try:
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]
    except KeyError:
        print("error:")
        pprint(data)
        exit(1)

    print("access_token:", access_token)
    print("refresh_token:", refresh_token)
    print("expires_in:", data.get("expires_in", 0))


def _login():
    code_verifier, code_challenge = oauth_pkce(s256)
    login_params = {
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "client": "pixiv-android",
    }

    open_url(f"{LOGIN_URL}?{urlencode(login_params)}")

    try:
        code = input("code: ").strip()
    except (EOFError, KeyboardInterrupt):
        return

    response = requests.post(
        AUTH_TOKEN_URL,
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code,
            "code_verifier": code_verifier,
            "grant_type": "authorization_code",
            "include_policy": "true",
            "redirect_uri": REDIRECT_URI,
        },
        headers={"User-Agent": USER_AGENT},
    )
    return response


def login():
    print_auth_token_response(_login())


def _refresh(refresh_token):
    return requests.post(
        AUTH_TOKEN_URL,
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token",
            "include_policy": "true",
            "refresh_token": refresh_token,
        },
        headers={"User-Agent": USER_AGENT},
    )


def refresh(refresh_token):
    print_auth_token_response(_refresh(refresh_token))


def main():
    parser = ArgumentParser()
    subparsers = parser.add_subparsers()
    parser.set_defaults(func=lambda _: parser.print_usage())
    login_parser = subparsers.add_parser("login")
    login_parser.set_defaults(func=lambda _: login())
    refresh_parser = subparsers.add_parser("refresh")
    refresh_parser.add_argument("refresh_token")
    refresh_parser.set_defaults(func=lambda ns: refresh(ns.refresh_token))
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
