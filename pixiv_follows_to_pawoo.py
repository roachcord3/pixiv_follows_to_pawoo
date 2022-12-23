#!/usr/bin/env python3
#
# original source: https://github.com/mierapid23/pixiv_follows_to_pawoo/blob/767d5f91ceb2ba07a0563532cfd21fa5ba7121c9/pixiv_follows_to_pawoo.py
#
# the original wasn't licensed, but the user hasn't updated it since the
# first commit, and they probably don't even speak english, so i doubt they
# would sue either you or I for using or distributing this extremely modified
# version. this was last edited in 2022
#
# as far as i'm concerned, if my own contributions can be licensed, they are
# licensed under the CNPL-NAv7+.

from pixivpy3 import *
import sys, os
import mastodon
import requests 
from time import sleep

# i have worked professionally with python for over 10 years and i still don't
# know a better way of doing "just give me the code from the file next to me"
import os.path
sys.path.append(os.getcwd())

from pixiv_auth import _login as pixiv_login, _refresh as pixiv_refresh


MASTO_DOMAIN = "pawoo.net"


def get_pixiv_token_login():
    # in case you already got a token by running pixiv_auth.py manually
    refresh_token = os.environ.get('REFRESH_TOKEN')
    if refresh_token:
        token_login = pixiv_refresh(refresh_token).json()
    else:
        try:
            with open("refresh_token.txt", "r") as f:
                refresh_token = f.read()
        except Exception as e:
            token_login = pixiv_login().json()
        else:
            token_login = pixiv_refresh(refresh_token).json()
    return token_login


def setup_pixiv():
    token_login = get_pixiv_token_login()
    # set up the pixiv api object
    aapi = AppPixivAPI()
    aapi.auth(refresh_token=token_login['refresh_token'])
    print(f"Successfully logged into pixiv with refresh token: {token_login['refresh_token']}")
    # it's really easy to get too much log output and miss out ont this, and it's
    # a PITA to get a new one
    with open("refresh_token.txt", "w") as f:
        f.write(token_login['refresh_token'])

    return aapi, token_login['user']['id']


def setup_mastodon():
    # set up a mastodon client for pawoo
    masto = mastodon.Mastodon(
        client_id = "mastodon_client_id.txt",
        access_token = "mastodon_access_token.txt",
        api_base_url = f"https://{MASTO_DOMAIN}",
        ratelimit_method = "pace",
    )
    print("Successfully logged into mastodon")
    return masto


def get_already_following(masto):
    # get a list of people you already follow (useful for avoiding rate limits)
    me = masto.me()
    already_following = set()
    page = masto.account_following(me['id'])
    while page is not None:
        # for some godforsaken reason, there is no attribute with the full
        # account name, including the leading @, so we have to add it for the
        # search to work later.
        already_following = already_following.union(
                f"@{acc['acct']}" if acc['acct'].endswith(MASTO_DOMAIN)
                else f"@{acc['acct']}@{MASTO_DOMAIN}"
                for acc in page
                )
        page = masto.fetch_next(page)
    print(f"Got {len(already_following)} mastodon accounts already followed")
    return already_following


def get_pixiv_following_uids(aapi, your_user_id):
    # get all the uids of everyone you're following
    # side note: why the hell is offset='' valid but it just gives you public
    uids = set()
    for r in ('public', 'private'):
        offset = 0
        while True:
            user_following = aapi.user_following(your_user_id, restrict=r, offset=offset)
            try:
                user_previews = user_following['user_previews']
            except KeyError:
                print(f"Got unexpected response from pixiv: {user_following}")
                raise

            uids = uids.union(i['user']['id'] for i in user_following['user_previews'] if 'user' in i)
            # whhhhhyyyyyy doesn't this SDK support pagination
            if user_following['next_url'] is None:
                break
            offset += len(user_previews)
    print(f"Got {len(uids)} pixiv users to check")
    return uids


# unlike the mastodon client, pixivpy has no rate limit handling i can find
def get_user_detail(aapi, uid):
    user_detail = aapi.user_detail(uid)
    sleep_backoff = 60
    while user_detail.get('error'):
        print(f"⚠️ Got an error when trying to look up uid {uid}: {user_detail['error']}")
        if user_detail['error']['user_message'] == 'Your access is currently restricted.':
            # I'm not 100% certain but I think the following API returns
            # deleted accounts sometimes, and that might be what this error
            # means. So, double check to make sure that the user's profile
            # exists by using something outside the API.
            resp = requests.get(f"https://www.pixiv.net/users/#{uid}")
            if resp.status_code != 200:
                print(f"🚫 User {uid} probably doesn't exist anymore (got a {resp.status_code} looking up their page), but for some reason is still in your following list. Skipping.")
                break
        elif user_detail['error']['message'] != 'Rate Limit':
            print(f"Unhandleable error: {user_detail['error']}")
            break
        print(f"Sleeping for {sleep_backoff:.1f} seconds and then redoing login before trying again")
        sleep(sleep_backoff)
        sleep_backoff **= 1.1
        # redo login, since if this backoff takes long enough, your creds might expire
        token_login = get_pixiv_token_login()
        aapi.auth(refresh_token=token_login['refresh_token'])
        user_detail = aapi.user_detail(uid)
    return user_detail


    # get what their actual username is (pixiv profiles don't include this)
def get_actual_pawoo_username(aapi, uid):
    user_detail = get_user_detail(aapi, uid)
    try:
        user = user_detail['user']
    except KeyError:
        print(f"⚠️ pixivpy barfed and gave us a weird user when looking up uid {uid}: {user_detail}")
        return

    user_str = f"{user['name']} (id: {user['id']}, account: {user['account']})"
    pixiv_pawoo_url = user_detail.get('profile', {}).get('pawoo_url')
    if pixiv_pawoo_url is None:
        print(f"{user_str} does not have a pawoo URL listed in their profile")
        return

    pawoo_url = requests.get(pixiv_pawoo_url)
    if pawoo_url.status_code != 200:
        print(f"⚠️ Couldn't lookup {user['name']}'s pawoo ID from the listed URL {pixiv_pawoo_url}, got a {pawoo_url.status_code} status code")
        return

    pawoo_username = f"{pawoo_url.url.lstrip(f'https://{MASTO_DOMAIN}/')}@{MASTO_DOMAIN}"
    print(f"🐘 {user_str} has the following pawoo username: {pawoo_username}")
    return pawoo_username


# if user has a pawoo account on their profile, try to follow it
def try_to_follow_pawoo_user(masto, pawoo_username):
    try:
        [pawoo_user_detail] = masto.account_search(pawoo_username, limit=1)
    except Exception as e:
        print(f"⚠️ Couldn't find {pawoo_username}'s pawoo account ID: {e}")
        return

    pawoo_num_id = pawoo_user_detail['id']
    try:
        follow_result = masto.account_follow(pawoo_num_id)
        if follow_result.following:
            print(f"✅ Followed {pawoo_username}")
        elif follow_result.requested:
            print(f"☑️ Sent follow request to {pawoo_username}")
    except Exception as e:
        print("🚫 Couldn't follow {pawoo_username} (id: {pawoo_num_id}): {e}")


# actually do the needful
def main():
    aapi, your_user_id = setup_pixiv()
    masto = setup_mastodon()
    already_following = get_already_following(masto)
    uids = get_pixiv_following_uids(aapi, your_user_id)

    for uid in uids:
        pawoo_username = get_actual_pawoo_username(aapi, uid)
        if pawoo_username is None:
            continue
        if pawoo_username in already_following:
            print(f"✅ You are already following {pawoo_username}")
            continue
        try_to_follow_pawoo_user(masto, pawoo_username)


if __name__ == "__main__":
    main()
