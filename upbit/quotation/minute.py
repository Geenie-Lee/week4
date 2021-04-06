import json

import requests


class Minute:
    def __init__(self):
        print(">> class: "+self.__class__.__name__)
        self.collect("KRW-DAWN", "5", 100)

    def collect(self, market, unit, cnt):
        url = "https://api.upbit.com/v1/candles/minutes/"+unit
        querystring = {"market": market, "count": cnt}
        response = requests.request("GET", url, params=querystring)
        minutes = json.loads(response.text)

        i = 0
        for minute in minutes:
            i = i+1
            print('>> minute[%s] => %s ' % (i, minute))


if __name__ == "__main__":
    Minute()