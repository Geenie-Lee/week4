from upbit.dao.market_sql import MarketSql
from upbit.database.connection import Connection


class MarketDao:
    def __init__(self):
        print(">> class: " + self.__class__.__name__)
        self.connection = Connection()
        self.query = MarketSql()

    def save(self, markets):
        for market in markets:
            self.delete(market)
            self.insert(market)
            print('>> saved => %s ' % market)

        self.connection.close()

    def delete(self, market):
        self.connection.cursor.execute(self.query.delete(), (market['market'], market['english_name']))

    def insert(self, market):
        self.connection.cursor.execute(self.query.insert(), (market['market'], market['korean_name'], market['english_name']))


if __name__ == "__main__":
    MarketDao()
