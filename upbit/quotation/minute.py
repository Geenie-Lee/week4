import json
import time

import requests


class Minute:
    def __init__(self):
        print(">> class: "+self.__class__.__name__)
        self.cnt = 0
        while True:
            self.collect("KRW-MED", "1", 1)
            time.sleep(5)

    def collect(self, market, unit, cnt):
        url = "https://api.upbit.com/v1/candles/minutes/"+unit
        querystring = {"market": market, "count": cnt}
        response = requests.request("GET", url, params=querystring)
        minutes = json.loads(response.text)

        self.cnt = self.cnt + 1
        for minute in minutes:
            print('>> %s trade_price = %s ' % (self.cnt, minute['trade_price']))


if __name__ == "__main__":
    Minute()