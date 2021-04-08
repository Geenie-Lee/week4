import psycopg2
from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QEventLoop, QTimer
from PyQt5.QtTest import QTest
import sys
import os
from datetime import datetime


class Trace(QAxWidget):

    def __init__(self):
        super().__init__()
        print(">>> class[Trace] start.")

        # 계좌 관련 변수들
        self.account_number = None
        self.password = "u23i4523"
        self.cert_password = "u23i4523R2"
        self.deposit = 0
        self.withdraw = 0

        # 스크린번호
        self.screen_number_market = "1000"  # 장 상태 체크 스크린번호
        self.screen_number_real = "3000"  # 실시간 스크린번호

        # 추적 종목
        self.trace_stocks = []
        self.current_stock_code = None
        self.today = (datetime.now()).strftime('%Y%m%d')

        # 추적 종목 딕셔너리(종목코드:고저갭가격)
        self.trace_stocks_dict = {}
        self.K = 0.5

        # 추적 종목 중 매수된 종목 관리
        self.trace_buy_stocks_dict = {}

        # 종가저장
        self.close_prices = []

        # event loop를 실행하기 위한 변수들
        self.event_loop_login = QEventLoop()
        self.event_loop_tr_data = QEventLoop()
        self.event_loop_real_data = QEventLoop()

        # ocx
        self.get_ocx_instance()

        # event slot
        self.event_slots()
        self.event_real_slots()

        # signal(로그인, 예수금, 잔고(종목), 미체결)
        self.signal_login()

        # 파일에서 분석된 종목 가져오기
        self.get_analyzed_stocks()

        # QTest.qWait(5000)
        QTimer.singleShot(1000, self.signal_market_status)  # 장 상태 체크

        # 대상 종목(보유,미체결,포트폴리오) 실시간 등록
        QTimer.singleShot(1000, self.all_stock_real_reg)

    def get_ocx_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    # 로그인, TR 이벤트 슬롯
    def event_slots(self):
        self.OnEventConnect.connect(self.slot_login)
        self.OnReceiveMsg.connect(self.slot_msg)

    # 실시간 이벤트 슬롯
    def event_real_slots(self):
        self.OnReceiveRealData.connect(self.slot_real_data)

    def signal_login(self):
        self.dynamicCall("CommConnect()")
        self.event_loop_login.exec_()

    def slot_login(self, error_code):
        print("")
        print(">>> function[slot_login] start >>>")
        print(">> 로그인(0:성공,-10:실패,-100:사용자정보교환실패,-101:서버접속실패): %s" % error_code)
        accounts = self.dynamicCall("GetLoginInfo(QString)", "ACCNO")
        self.account_number = accounts.split(";")[0]
        print(">> 계좌번호(%s자리): %s" % (len(self.account_number), self.account_number))
        self.event_loop_login.exit()
        print(">>> function[slot_login] end <<<")

    def signal_market_status(self):
        # [장시작시간][장운영구분] (0:장시작전, 2:장종료전(20분), 3:장시작, 4,8:장종료(30분), 9:장마감)
        value = self.dynamicCall("SetRealReg(QString, QString, int, QString)", self.screen_number_market, ' ', 215, "0")
        print(">> [장시작시간][장운영구분] (0:장시작전, 2:장종료전(20분), 3:장시작, 4,8:장종료(30분), 9:장마감)")
        print(">> value: %s" % value)
        self.event_loop_real_data.exec_()

    def get_analyzed_stocks(self):
        print("")
        if os.path.exists("files/analysis.txt"):
            f = open("files/analysis.txt", "r", encoding="utf8")

            lines = f.readlines()
            for line in lines:
                if line != "":
                    ls = line.split("\t")
                    stock_code = ls[0]
                    hl_gap_price = int(ls[1])
                    stock_name = ls[2].strip('\n')

                    self.trace_stocks_dict[stock_code] = hl_gap_price
                    print(">> 추적대상 종목코드: %s, 종목명: %s, 고저차이가격: %s" % (stock_code, stock_name, hl_gap_price))

                    self.trace_stocks.append(stock_code)

            # print(">> self.portfolio_stock_dict: %s" % self.portfolio_stock_dict)
            print(self.trace_stocks_dict)
            f.close()

    # 대상 종목(보유,미체결,포트폴리오) 실시간 등록
    def all_stock_real_reg(self):
        for stock_code in self.trace_stocks:
            fids = "20;10;12;15;16;17;18"
            self.dynamicCall("SetRealReg(QString, QString, QString, QString)", self.screen_number_real, stock_code, fids, "1")

            self.current_stock_code = stock_code
            if os.path.exists("files/" + self.current_stock_code + "_" + self.today + ".txt") == False:
                f = open("files/" + self.current_stock_code + "_" + self.today + ".txt", "w", encoding="utf8")

    def slot_real_data(self, stock_code, real_type, real_data):

        if real_type == "장시작시간":

            # 215:장운영구분, 20:체결시간, 214:장시작예상잔여시간
            market_op_type = self.dynamicCall("GetCommRealData(QString, int)", stock_code, 215)
            conclusion_time = self.dynamicCall("GetCommRealData(QString, int)", stock_code, 20)
            market_open_remain_time = self.dynamicCall("GetCommRealData(QString, int)", stock_code, 214)

            if market_op_type == "0":
                print(">> [%s]장 시작 전" % market_op_type)
            elif market_op_type == "3":
                print(">> [%s]장 시작" % market_op_type)
            elif market_op_type == "2":
                print(">> [%s]장 종료, 동시호가로 넘어감" % market_op_type)
            elif market_op_type == "4":
                print(">> [%s]15시 30분 장 종료" % market_op_type)

                # 실시간 연결 모두 끊기
                for code in self.portfolio_stock_dict.keys():
                    self.dynamicCall("SetRealRemove(QString, QString)", self.screen_number_market, code)
                    print(">> 종목코드[%s] 실시간 연결 종료." % code)

                # 다음 날을 위한 종목분석 시작
                QTest.qWait(1000)
                # self.file_delete() # 초기화(포트폴리오) 파일삭제 또는 디비 삭제
                # self.calculate_fnc() # 종목분석(알고리즘 적용) 후 파일 또는 디비 저장

                # 프로그램 종료
                sys.exit()

            print(">> market_op_type: %s" % market_op_type)
            print(">> conclusion_time: %s" % str(datetime.date(conclusion_time)))
            print(">> market_open_remain_time %s" % str(datetime.date(market_open_remain_time)))

        elif real_type == "주식체결":

            """
                [20] = 체결시간
                [10] = 현재가
                [11] = 전일대비
                [12] = 등락율
                [27] = (최우선)매도호가
                [28] = (최우선)매수호가
                [15] = 거래량
                [13] = 누적거래량
                [14] = 누적거래대금
                [16] = 시가
                [17] = 고가
                [18] = 저가
                [25] = 전일대비기호
                [26] = 전일거래량대비(계약,주)
                [29] = 거래대금증감
                [30] = 전일거래량대비(비율)
                [31] = 거래회전율
                [32] = 거래비용
                [228] = 체결강도
                [311] = 시가총액(억)
                [290] = 장구분
                [691] = KO접근도
                [567] = 상한가발생시간
                [568] = 하한가발생시간            
            """

            conclusion_time = self.dynamicCall("GetCommRealData(QString, in)", stock_code, 20).strip()
            close_price = self.dynamicCall("GetCommRealData(QString, in)", stock_code, 10).strip()
            net_change = self.dynamicCall("GetCommRealData(QString, in)", stock_code, 11).strip()
            fluctuation_rate = self.dynamicCall("GetCommRealData(QString, in)", stock_code, 12).strip()
            first_ask_price = self.dynamicCall("GetCommRealData(QString, in)", stock_code, 27).strip()
            first_bid_price = self.dynamicCall("GetCommRealData(QString, in)", stock_code, 28).strip()
            volume = self.dynamicCall("GetCommRealData(QString, in)", stock_code, 15).strip()
            cumulative_volume = self.dynamicCall("GetCommRealData(QString, in)", stock_code, 13).strip()
            high_price = self.dynamicCall("GetCommRealData(QString, in)", stock_code, 17).strip()
            open_price = self.dynamicCall("GetCommRealData(QString, in)", stock_code, 16).strip()
            low_price = self.dynamicCall("GetCommRealData(QString, in)", stock_code, 18).strip()

            close_price = abs(int(close_price))
            net_change = abs(int(net_change))
            fluctuation_rate = float(fluctuation_rate)
            first_ask_price = abs(int(first_ask_price))
            first_bid_price = abs(int(first_bid_price))
            volume = abs(int(volume))
            cumulative_volume = abs(int(cumulative_volume))
            high_price = abs(int(high_price))
            open_price = abs(int(open_price))
            low_price = abs(int(low_price))
            hl_gap_price = self.trace_stocks_dict[stock_code]

            # 변동성 돌파 매매의 매수 가격 계산하기
            calc_buy_price = open_price+(hl_gap_price*self.K)

            tm = conclusion_time[:4]

            # 금액 분포 테이블에 저장
            self.insert_freq_info(stock_code, close_price, volume, tm)

            # 변동성 돌파 전략에 따른 가격 돌파 시 매수
            if calc_buy_price <= close_price and self.trace_buy_stocks_dict[stock_code] != 'Y':
                print(">> 변동성 돌파에 의해 종목[%s]이 %s 원에 매수되었습니다." % (stock_code, close_price))
                # 매수되었음을 기록해서 중복 매수 방지
                self.trace_buy_stocks_dict[stock_code] = 'Y'
                # 매수된 가격을 테이블의 매수여부에 업데이트해서 수익율 체크
                self.update_buy_flag(stock_code, close_price)


            #             print(">> 체결시간: %s" % conclusion_time)
            #             print(">> 현재가: %s" % format(close_price, ","))
            #             print(">> 전일대비: %s" % format(net_change, ","))
            #             print(">> 등락율: %s" % fluctuation_rate)
            #             print(">> (최우선)매도호가: %s" % format(first_ask_price, ","))
            #             print(">> (최우선)매수호가: %s" % format(first_bid_price, ","))
            #             print(">> 거래량: %s" % format(volume, ","))
            #             print(">> 누적거래량: %s" % format(cumulative_volume, ","))
            #             print(">> 고가: %s" % format(high_price, ","))
            #             print(">> 시가: %s" % format(open_price, ","))
            #             print(">> 저가: %s" % format(low_price, ","))

            first_price = round(high_price - (high_price * 0.075))
            second_price = round(high_price - (high_price * 0.050))
            third_price = round(high_price - (high_price * 0.025))

            #             print(">> 종가목록 길이 = %s" % len(self.close_prices))

            # 변곡점 체크
            if len(self.close_prices) > 0:

                # 고가+저가 평균 가격구하기
                hl_price = round((high_price + low_price) / 2)

                # 평균가격 구하기
                avg_price = 0
                tot_price = 0
                for cp in self.close_prices:
                    tot_price += cp

                avg_price = round(tot_price / len(self.close_prices))

                # 체결 최근 50 개중 가장 낮은 가격의 경우 매수

                # 체결 최근 50 개중 가장 높은 가격의 경우 매도

                # 목표 수량 설정

                # 목표 수량 이내의 경우 매수(한호가 위로. 최우선 매도호가로 매수)

                # 목표 수량 확보 시 매도 타이밍 노림(한호가 아래로. 최우선 매수호가로 매도)

                #                 if close_price > self.close_prices[len(self.close_prices)-1]:
                print(
                    "%s> %s    현재가: %s, 시가: %s, 고가: %s, 저가: %s, HL가: %s, 평균가: %s, 1차매수가: %s, 2차매수가: %s, 3차매수가: %s, 거래량: %s" % (
                    conclusion_time, stock_code, format(close_price, ","), format(open_price, ","),
                    format(high_price, ","), format(low_price, ","), format(hl_price, ","), format(avg_price, ","),
                    format(first_price, ","), format(second_price, ","), format(third_price, ","), format(volume, ",")))

                # if os.path.exists("files/" + self.current_stock_code + "_" + self.today + ".txt"):
                #     f = open("files/" + self.current_stock_code + "_" + self.today + ".txt", "a")
                #     f.write("%s> %s    현재가: %s, 시가: %s, 고가: %s, 저가: %s, HL가: %s, 평균가: %s, 거래량: %s" % (
                #     conclusion_time, stock_code, format(close_price, ","), format(open_price, ","),
                #     format(high_price, ","), format(low_price, ","), format(hl_price, ","), format(avg_price, ","),
                #     format(volume, ",")))
                #     f.write("\n")
                #     f.close()

            self.close_prices.append(close_price)

        #         self.disconnect_screen_number(self.screen_number_market)
        self.event_loop_real_data.exit()

    def slot_msg(self, screen_number, rq_name, tr_code, msg):
        print("> screen_number: %s, rq_name: %s, tr_code: %s, msg: %s," % (screen_number, rq_name, tr_code, msg))

    def disconnect_screen_number(self, screen_number=None):
        self.dynamicCall("DisconnectRealData(QString)", screen_number)

    def insert_freq_info(self, stock_code, close_price, volume, tm):
        conn_string = "host='localhost' dbname='postgres' user='postgres' password='postgres' port='5432'"
        conn = psycopg2.connect(conn_string)
        cur = conn.cursor()

        select_cfreq_sql = "select volume,freq from stock_rtm_cfreq where dt = to_char(current_date,'yyyymmdd') and stock_code = %s and price = %s"
        cur.execute(select_cfreq_sql, (stock_code, close_price,))
        row = cur.fetchone()

        update_cfreq_sql = "update stock_rtm_cfreq set iscur = %s where dt = to_char(current_date,'yyyymmdd') and stock_code = %s"
        cur.execute(update_cfreq_sql, ('N', stock_code))

        if row is None:
            insert_cfreq_sql = "insert into stock_rtm_cfreq(stock_code,dt,tm,price,volume,freq,iscur) values (%s,%s,%s,%s,%s,%s,%s)"
            cur.execute(insert_cfreq_sql, (stock_code, self.today, tm, close_price, volume, 1, 'Y'))
        else:
            update_cfreq_sql = "update stock_rtm_cfreq set tm = %s, volume = %s, freq = %s, iscur = %s where dt = to_char(current_date,'yyyymmdd') and stock_code = %s and price = %s"
            cur.execute(update_cfreq_sql, (tm, row[0]+volume, row[1]+1, 'Y', stock_code, close_price))

        conn.commit()
        cur.close()
        conn.close()

    def update_buy_flag(self, stock_code, close_price):
        conn_string = "host='localhost' dbname='postgres' user='postgres' password='postgres' port='5432'"
        conn = psycopg2.connect(conn_string)
        cur = conn.cursor()

        update_cfreq_sql = "update stock_rtm_cfreq set isbuy = %s where dt = to_char(current_date,'yyyymmdd') and stock_code = %s and price = %s"
        cur.execute(update_cfreq_sql, ('Y', stock_code, close_price))

        conn.commit()
        cur.close()
        conn.close()
