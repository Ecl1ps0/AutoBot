import itertools
import random
import string

import configs
from api import APIClient
from bots import OutlookBot, LinkedInBot, TwitterBot


def main():
    client = APIClient(configs.access_token_payload)

    # proxies = client.get_proxies(configs.us_proxy_params)
    # for proxy in proxies:
    #     email = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8)) + '@1secmail.com'
    #
    #     bot = TwitterBot(client, proxy=proxy)
    #     bot.create_new_token(email)

    # static_proxies = client.get_proxies(configs.us_proxy_params)
    #
    # for proxy in static_proxies:
    #     email = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8)) + '@1secmail.com'
    #
    #     bot = OutlookBot(client, proxy=proxy)
    #     bot.create_new_token(email)

    tokens = client.get_tokens(configs.linkedin_tokens_params)
    static_proxies = client.get_proxies(configs.us_proxy_params)

    for token, proxy in itertools.zip_longest(tokens, static_proxies):
        bot = LinkedInBot(client, token, proxy)
        bot.update_token_to_active()

    # dynamic_proxies = client.get_proxies(params=configs.dynamic_proxy_params)
    #
    # for proxy in dynamic_proxies:
    #     email = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8)) + '@1secmail.com'
    #
    #     bot = LinkedInBot(client, proxy=proxy)
    #     bot.create_new_token(email)
    

if __name__ == '__main__':
    main()
