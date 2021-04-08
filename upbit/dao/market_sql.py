
class MarketSql:

    def __init__(self):
        print("")

    def insert(self):
        sql = "insert into coin_market(market,korean_name,english_name) values (%s,%s,%s)"
        return sql

    def delete(self):
        sql = "delete from coin_market where market = %s and english_name = %s"
        return sql
