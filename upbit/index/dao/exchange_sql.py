
class ExchangeSql:

    def __init__(self):
        print("")

    def exist(self):
        sql = "select dt,tm,currency,price,freq,iscur from exchange where dt = to_char(current_date,'yyyymmdd') and " \
              "currency = '미국 USD' and price = %s "
        return sql

    def init(self):
        sql = "update exchange set iscur = 'N' where currency = '미국 USD'"
        return sql

    def update(self):
        sql = "update exchange set tm = %s, freq = %s, iscur = %s where dt = to_char(current_date,'yyyymmdd') and " \
              "currency = '미국 USD' and price = %s "
        return sql

    def insert(self):
        sql = "insert into exchange(dt,tm,currency,price,freq,iscur) values (%s,%s,%s,%s,%s,%s)"
        return sql