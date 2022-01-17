"""
    Copyright 2021 t.me/hikariakami
    Licensed under the Apache License, Version 2.0
    
    Author is not responsible for any consequencies caused by using this
    software or any of its parts. If you have any questions or wishes, feel
    free to contact Dan by sending pm to @hikari_alt.
"""

#<3 title: NSFW
#<3 pic: https://img.icons8.com/fluency/48/000000/keep-away-from-children.png
#<3 desc: Кидает рандомную картинку NSFW содержания с scroller

from .. import loader, utils
import requests
import json
import io
import telethon
import os
import logging

# requires: requests

logger = logging.getLogger(__name__)

@loader.tds
class NSFWMod(loader.Module):
    strings = {
        "name": "NSFW", 
        "sreddit404": "🦊 <b>Subreddit not found</b>",
        "default_subreddit": "🦊 <b>Set new default subreddit: </b><code>{}</code>", 
        "loading": "🦊 <b>Loading...</b>"
    }

    async def client_ready(self, client, db):
        self.db = db
        self.client = client

    async def nsfwcmd(self, message):
        """<subreddit | default> [-n <quantity | 1 by default>] - Send random NSFW picture"""
        args = utils.get_args_raw(message)
        message = await utils.answer(message, self.strings('loading', message))
        try:
            message = message[0]
        except:
            pass

        if '-n' in args:
            try:
                quantity = int(args[args.find('-n') + 2:])
            except:
                quantity = 1

            args = args[:args.find('-n')]
        else:
            quantity = 1

        args = args.strip()

        if not args:
            args = self.db.get('NSFW', 'default_subreddit', 'nsfw')

        subreddit = f"/r/{args}"

        logger.info(f'[NSFW]: Fetching {quantity} photos from {subreddit}')

        ans = requests.get(f'https://api.scrolller.com{subreddit}')
        if ans.status_code != 200:
            await utils.answer(message, self.strings('sreddit404', message))
            return

        ans = requests.get('https://api.scrolller.com/api/v2/graphql', json={
            "query": " query SubredditQuery( $url: String! $filter: SubredditPostFilter $iterator: String ) { getSubreddit(url: $url) { children( limit: " + str(quantity) + " iterator: $iterator filter: $filter disabledHosts: null ) { iterator items { __typename url title subredditTitle subredditUrl redditPath isNsfw albumUrl isFavorite mediaSources { url width height isOptimized } } } } } ",
            "variables": {"url": subreddit, "filter": None, "hostsDown": None},
            "authorization": None
        }).json()
        # logger.info(ans)
        posts = ans['data']['getSubreddit']['children']['items']
        res = []
        for i in range(min(quantity, len(posts))):
            url = posts[i]['mediaSources'][0]['url']
            fname = url.split('/')[-1]
            open(f'/tmp/{fname}', 'wb').write(requests.get(url).content)
            res.append(f'/tmp/{fname}')

        if quantity == 1:
            title = posts[0]['title']
        else:
            title = f"{quantity} photos from subreddit {subreddit}"
        await self.client.send_file(utils.get_chat_id(message), file=res, caption='<i>' + utils.escape_html(title) + '</i>', parse_mode="HTML")
        for path in res:
            try:
                os.remove(path)
            except:
                pass
        await message.delete()

    async def nsfwcatcmd(self, message):
        """<subreddit> - Set new default subreddit"""
        args = utils.get_args_raw(message)
        if not args:
            args = "nsfw"

        ans = requests.get(f'https://api.scrolller.com/r/{args}')
        if ans.status_code != 200:
            await utils.answer(message, self.strings('sreddit404', message))
            return

        self.db.set('NSFW', 'default_subreddit', args)
        await utils.answer(message, self.strings('default_subreddit', message).format(args))
