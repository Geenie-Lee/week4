import urllib.request
from bs4 import BeautifulSoup

from upbit.index.dao.exchange_dao import ExchangeDao


class Exchange:

    def __init__(self):
        self.url = "http://finance.naver.com/marketindex/exchangeList.nhn"
        self.price = 0
        self.dao = ExchangeDao()
        self.collect()

    def collect(self):
        fp = urllib.request.urlopen(self.url)
        source = fp.read()
        fp.close()
        class_list = ["tit", "sale"]
        soup = BeautifulSoup(source, 'html.parser')
        soup = soup.find_all("td", class_=class_list)
        money_data = {}

        for data in soup:
            if soup.index(data) % 2 == 0:
                data = data.get_text().replace('\n', '').replace('\t', '')
                money_key = data
            elif soup.index(data) % 2 == 1:
                money_value = data.get_text()
                if money_key == '미국 USD':
                    self.price = money_value.replace(',','')    # float(aa.replace(',',''))
                    money_data[money_key] = money_value

        self.dao.upsert(self.price)


if __name__ == "__main__":
    Exchange()