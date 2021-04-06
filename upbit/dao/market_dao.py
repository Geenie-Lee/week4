from upbit.database.connection import Connection


class MarketDao:
    def __init__(self):
        print(">> class: " + self.__class__.__name__)
        self.connection = Connection()

    def save(self, markets):
        for market in markets:
            self.delete(market)
            self.insert(market)
            print('>> saved => %s ' % market)

        self.connection.close()

    def delete(self, market):
        sql = "delete from coin_market where market = %s and english_name = %s"
        self.connection.cursor.execute(sql, (market['market'], market['english_name']))

    def insert(self, market):
        sql = "insert into coin_market(market,korean_name,english_name) values (%s,%s,%s)"
        self.connection.cursor.execute(sql, (market['market'], market['korean_name'], market['english_name']))


if __name__ == "__main__":
    # simulator 클래스 호출
    MarketDao()
