import configparser
import os
import jwt
import uuid
import hashlib
import requests

from urllib.parse import urlencode


class Account:
    def __init__(self):
        print(">> class: "+self.__class__.__name__)
        self.url = "https://api.upbit.com/v1/accounts"
        self.access_key = "zMAxBxd4puUtZgRTMbOxR0iE8O2OhaohxltmiSxR"
        self.secret_key = "36DHxC7tbMFi8STR51zTkNbWooRz1HZGZpxQ2xIL"
        self.info()

    def info(self):
        payload = {
            'access_key': self.access_key,
            'nonce': str(uuid.uuid4()),
        }

        jwt_token = jwt.encode(payload, self.secret_key)
        authorize_token = 'Bearer {}'.format(jwt_token)
        headers = {"Authorization": authorize_token}

        res = requests.get(self.url, headers=headers)

        print(res.json())


if __name__ == "__main__":
    Account()