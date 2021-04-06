import json
import datetime
import requests


class Day:
    def __init__(self):
        print(">> class: " + self.__class__.__name__)
        self.now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.collect("KRW-DAWN", 5)

    def collect(self, market, days):
        url = "https://api.upbit.com/v1/candles/days"
        querystring = {"market": market, "to": self.now, "count": days}
        response = requests.request("GET", url, params=querystring)
        days = json.loads(response.text)

        i = 0
        for day in days:
            i = i+1
            print('>> day[%s] => %s ' % (i, day))


if __name__ == "__main__":
    Day()
