import requests
import json

from upbit.dao.market_dao import MarketDao


class Market:

    def __init__(self):
        self.url = "https://api.upbit.com/v1/market/all"
        self.dao = MarketDao()
        self.collect()

    def collect(self):
        querystring = {"isDetails": "false"}
        response = requests.request("GET", self.url, params=querystring)
        self.dao.save(json.loads(response.text))


if __name__ == "__main__":
    Market()
