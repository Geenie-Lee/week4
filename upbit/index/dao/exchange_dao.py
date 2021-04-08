from datetime import datetime

from upbit.database.connection import Connection
from upbit.index.dao.exchange_sql import ExchangeSql


class ExchangeDao:
    def __init__(self):
        print(">> class: "+self.__class__.__name__)
        self.connection = Connection()
        self.query = ExchangeSql()
        self.today = (datetime.now()).strftime('%Y%m%d')
        self.tm = (datetime.now()).strftime('%H%M')

    def upsert(self, price):
        self.init()
        currency = self.exist(price)

        if currency is None:
            self.insert(price)
        else:
            self.update(currency)

        self.connection.conn.commit()
        self.connection.close()

    def exist(self, price):
        print(">> %s:%s => %s" % (self.tm[:2], self.tm[2:], price))
        self.connection.cursor.execute(self.query.exist(), (price,))
        return self.connection.cursor.fetchone()

    def init(self):
        self.connection.cursor.execute(self.query.init())

    def update(self, currency):
        self.connection.cursor.execute(self.query.update(), (self.tm, currency[4]+1, 'Y', currency[3]))

    def insert(self, price):
        self.connection.cursor.execute(self.query.insert(), (self.today, self.tm, '미국 USD', price, 1, 'Y'))


if __name__ == "__main__":
    ExchangeDao()
