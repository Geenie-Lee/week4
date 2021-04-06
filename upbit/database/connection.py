import configparser

import psycopg2


class Connection:
    def __init__(self):
        print(">> class: "+self.__class__.__name__)
        self.host = None
        self.dbname = None
        self.user = None
        self.password = None
        self.port = None

        self.conn = None
        self.cursor = None

        self.load_conf()
        self.connect()

    def load_conf(self):
        config = configparser.ConfigParser()
        config.read('config.ini')

        self.host = config['repos']['host']
        self.dbname = config['repos']['dbname']
        self.user = config['repos']['user']
        self.password = config['repos']['password']
        self.port = config['repos']['port']

    def connect(self):
        conn_string = "host='%s' dbname='%s' user='%s' password='%s' port=%s" % \
                      (self.host, self.dbname, self.user, self.password, self.port)

        if self.conn is None:
            self.conn = psycopg2.connect(conn_string)
            self.cursor = self.conn.cursor()

    def close(self):
        if self.cursor is not None:
            self.cursor.close()
        if self.conn is not None:
            self.conn.close()


if __name__ == "__main__":
    # simulator 클래스 호출
    Connection()
