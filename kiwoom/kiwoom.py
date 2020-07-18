from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QEventLoop, QTimer
from PyQt5.QtTest import QTest
import sys
import os
import datetime


class Kiwoom(QAxWidget):

    def __init__(self):
        super().__init__()
        print(">>> class[Kiwoom] start.")

        # 계좌 관련 변수들
        self.account_number = None
        self.password = "u23i4523"
        self.cert_password = "u23i4523R2"
        self.deposit = 0
        self.withdraw = 0

        # 스크린번호
        self.screen_number_market = "1000"  # 장 상태 체크 스크린번호
        self.screen_number_account = "2000"  # 계좌 관련 스크린번호
        self.screen_number_real = "3000"  # 실시간 스크린번호
        self.screen_number_anal = "4000"  # 분석용 스크린번호
        self.screen_number_stock = "5000"  # 종목별 스크린번호
        self.screen_number_order = "6000"  # 주문용 스크린번호

        # 종목 리스트
        self.all_stock_dict = {}
        self.account_stock_dict = {}
        self.outstanding_stock_dict = {}
        self.portfolio_stock_dict = {}
        self.balance_stock_dict = {}  # 잔고

        # event loop를 실행하기 위한 변수들
        self.event_loop_login = QEventLoop()
        self.event_loop_tr_data = QEventLoop()
        self.event_loop_real_data = QEventLoop()

        # ocx
        self.get_ocx_instance()

        # event slot
        self.event_slots()
        self.event_real_slots()
        self.event_condition_slots()

        # signal(로그인, 예수금, 잔고(종목), 미체결)
        self.signal_login()
        self.signal_deposit_info()
        self.signal_balance_info()
        self.signal_condition_info()

        QTimer.singleShot(5000, self.signal_outstanding_info)  # 5초 후 실시간미체결요청(opt10075)
        
        # 파일에서 분석된 종목 가져오기
        self.get_analyzed_stocks()

        # QTest.qWait(10000)
        QTimer.singleShot(10000, self.set_screen_number)

        # QTest.qWait(5000)
        QTimer.singleShot(15000, self.signal_market_status)  # 장 상태 체크

        # 대상 종목(보유,미체결,포트폴리오) 실시간 등록
        QTimer.singleShot(20000, self.all_stock_real_reg)

    def get_ocx_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    # 로그인, TR 이벤트 슬롯
    def event_slots(self):
        self.OnEventConnect.connect(self.slot_login)
        self.OnReceiveTrData.connect(self.slot_tr_data)
        self.OnReceiveMsg.connect(self.slot_msg)

    # 실시간 이벤트 슬롯
    def event_real_slots(self):
        self.OnReceiveRealData.connect(self.slot_real_data)
        self.OnReceiveChejanData.connect(self.slot_chejan_data)

    # 조건검색 이벤트 슬롯
    def event_condition_slots(self):
        self.OnReceiveConditionVer.connect(self.slot_condition)
        self.OnReceiveTrCondition.connect(self.slot_tr_condition)
        self.OnReceiveRealCondition.connect(self.slot_real_condition)

    def slot_condition(self, ret, msg):
        print("")
        print(">>>>>>>>>>>>>>>>>>>>>>>> 조건검색식[S] >>>>>>>>>>>>>>>>>>>>>>>>>>>")
        # print(">> ret: %s" % ret)
        # print(">> msg: %s" % msg)
            
        condition_name_list = self.dynamicCall("GetConditionNameList()").split(";")[:-1]
        for condition in condition_name_list:
            index = int(condition.split("^")[0])
            condition_name = condition.split("^")[1]
            print(">> [%s]:[%s]" % (index, condition_name))

            ok = self.dynamicCall("SendCondition(QString, QString, int, int)", "0156", condition_name, index, 1)

        print(">>>>>>>>>>>>>>>>>>>>>>>> 조건검색식[E] >>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print("")

    # 나의 조건식 받기
    def slot_tr_condition(self, screen_number, code_list, condition_name, index, prev_next):
        print("")
        # print(">> screen_number: %s" % screen_number)
        # print(">> code_list: %s" % code_list)
        print(">> [%s]:%s" % (index, condition_name))
        # print(">> index: %s" % index)
        # print(">> prev_next: %s" % prev_next)

        code_list = code_list.split(";")[:-1]
        for code in code_list:
            code_name = self.dynamicCall("GetMasterCodeName(QString)", code).strip()
            print(">> %s: %s" % (code, code_name))

    def slot_real_condition(self, stock_code, event_type, condition_name, index):
        print("")

        if event_type == "I":
            stock_name = self.dynamicCall("GetMasterCodeName(QString)", stock_code)
            print(">> [%s]조건검색명: %s, 종목코드: %s, 종목명: %s, 종목편입: %s" % (index, condition_name, stock_code, stock_name, event_type))
        elif event_type == "D":
            print(">> [%s]조건검색명: %s, 종목코드: %s, 종목명: %s, 종목이탈: %s" % (index, condition_name, stock_code, stock_name, event_type))

    # HTS 조건식 로딩 (OnReceiveConditionVer() 호출)
    def signal_condition_info(self):
        self.dynamicCall("GetConditionLoad()")

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
        print("")
        print("")

        # [장시작시간][장운영구분] (0:장시작전, 2:장종료전(20분), 3:장시작, 4,8:장종료(30분), 9:장마감)
        value = self.dynamicCall("SetRealReg(QString, QString, int, QString)", self.screen_number_market, ' ', 215, "0")
        print(">> value: %s" % value)
        print("")
        self.event_loop_real_data.exec_()

    # opw00001: 예수금상세현황요청
    # INPUT: 계좌번호, 비밀번호, 비밀번호입력매체구분, 조회구분
    # OUTPUT[S]: 예수금상세현황
    def signal_deposit_info(self, prev_next="0"):
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_number)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호", self.password)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "예수금상세현황요청", "opw00001", prev_next,
                         self.screen_number_account)
        self.event_loop_tr_data.exec_()

    # opw00018: 계좌평가잔고내역요청
    # INPUT: 계좌번호, 비밀번호, 비밀번호입력매체구분, 조회구분
    # OUTPUT[S]: 계좌평가결과
    # OUTPUT[M]: 계좌평가잔고합산
    def signal_balance_info(self, prev_next="0"):
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_number)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호", self.password)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "계좌평가잔고내역요청", "opw00018", prev_next,
                         self.screen_number_account)
        self.event_loop_tr_data.exec_()

    # opt10075: 실시간미체결요청
    # INPUT: 계좌번호, 전체종목구분(0:전체,1:종목), 매매구분(0:전체,1:매도,:매수), 종목코드, 체결구분(0:전체,1:미체결,2:체결)
    # OUTPUT[S]: 계좌평가결과
    # OUTPUT[M]: 계좌평가잔고합산
    def signal_outstanding_info(self, prev_next="0"):
        print("")
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_number)
        self.dynamicCall("SetInputValue(QString, QString)", "매매구분", "0")
        self.dynamicCall("SetInputValue(QString, QString)", "체결구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "실시간미체결요청", "opt10075", prev_next,
                         self.screen_number_account)
        self.event_loop_tr_data.exec_()

    def get_analyzed_stocks(self):
        print("")
        if os.path.exists("files/analysis.txt"):
            f = open("files/analysis.txt", "r", encoding="utf8")

            lines = f.readlines()
            for line in lines:
                if line != "":
                    ls = line.split("\t")
                    stock_code = ls[0]
                    stock_name = ls[1]
                    close_price = abs(int(ls[2].split("\n")[0]))

                    self.portfolio_stock_dict.update({stock_code: {"종목명": stock_name, "현재가": close_price}})
                    my_price = round(close_price - (close_price * 0.01))
                    print(">> 종목코드: %s, 종목명: %s, 현재가: %s, 매입희망가: %s" % (stock_code, stock_name, close_price, my_price))

            # print(">> self.portfolio_stock_dict: %s" % self.portfolio_stock_dict)
            print("")
            f.close()

    def slot_tr_data(self, screen_number, rq_name, tr_code, record_name, prev_next):
        print("")
        print(">>> function[slot_tr_data] start >>>")
        print("> p1.screen_number: %s" % screen_number)
        print("> p2.rq_name: %s" % rq_name)
        print("> p3.tr_code: %s" % tr_code)
        print("> p4.record_name: %s" % record_name)
        print("> p5.prev_next: %s" % prev_next)

        # opw00001: 예수금상세현황요청
        if tr_code == "opw00001":
            deposit = self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, 0, "예수금").strip()
            withdraw = self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, 0, "출금가능금액").strip()
            
            self.deposit = int(deposit)
            self.withdraw = int(withdraw)
            
            print("")
            print(">> 예수금: %s" % format(self.deposit, ","))
            print(">> 출금가능금액: %s" % format(self.withdraw, ","))

        # opw00018: 계좌평가잔고내역요청
        elif tr_code == "opw00018":
            # single (총매입금액,총평가손익금액,총수익률(%),조회건수)

            total_purchase_amount = self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, 0, "총매입금액").strip()
            total_profit_loss_amount = self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, 0, "총평가손익금액").strip()
            total_earning_rate = self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, 0, "총수익률(%)").strip()
            hit_number = self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, 0, "조회건수").strip()

            print("")
            print(">> 총매입금액: %s" % format(int(total_purchase_amount), ","))
            print(">> 총평가손익금액: %s" % format(int(total_profit_loss_amount), ","))
            print(">> 총수익률(%%): %s" % float(total_earning_rate))
            print(">> 조회건수: %s" % int(hit_number))
            print("")

            # multi
            rows = self.dynamicCall("GetRepeatCnt(QString, QString)", tr_code, rq_name)
            print(">> 계좌평가잔고내역요청.보유 종목 건수: %s" % rows)

            # 종목번호, 종목명, 보유수량, 매입가, 매입금액, 매매가능수량, 수익률(%), 현재가, 전일종가
            for i in range(rows):
                stock_code = self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "종목번호").strip()[1:]
                stock_name = self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "종목명").strip()
                retention_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "보유수량").strip()
                purchase_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i,"매입가").strip()
                purchase_amount = self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "매입금액").strip()
                tradable_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "매매가능수량").strip()
                earning_rate = self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "수익률(%)").strip()
                close_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "현재가").strip()
                last_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "전일종가").strip()
                tax = self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "세금").strip()

                if stock_code in self.account_stock_dict:
                    pass
                else:
                    self.account_stock_dict[stock_code] = {}

                self.account_stock_dict[stock_code].update({"종목명": stock_name})
                self.account_stock_dict[stock_code].update({"보유수량": int(retention_quantity)})
                self.account_stock_dict[stock_code].update({"매입가": int(purchase_price)})
                self.account_stock_dict[stock_code].update({"수익률(%)": float(earning_rate)})
                self.account_stock_dict[stock_code].update({"현재가": int(close_price)})
                self.account_stock_dict[stock_code].update({"매입금액": int(purchase_amount)})
                self.account_stock_dict[stock_code].update({"매매가능수량": int(tradable_quantity)})

                print(">> self.account_stock_dict: %s" % self.account_stock_dict)

        # opt10075: 실시간미체결요청
        elif tr_code == "opt10075":
            rows = self.dynamicCall("GetRepeatCnt(QString, QString)", tr_code, rq_name)
            print("")
            print(">> 미체결 종목 건수: %s" % rows)
            # 종목코드, 종목명, 주문번호, 주문상태, 주문수량, 주문가격, 주문구분, 미체결수량, 체결량
            for i in range(rows):
                order_number = self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "주문번호").strip()
                stock_code = self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "종목코드").strip()
                stock_name = self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "종목명").strip()
                order_status = self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "주문상태").strip()  # 접수,확인,체결
                order_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "주문수량").strip()
                order_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "주문가격").strip()
                order_type = self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "주문구분").strip().lstrip("+").lstrip("-")
                outstanding_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "미체결수량").strip()
                conclusion_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, rq_name, i, "체결량").strip()

                if order_number in self.outstanding_stock_dict:
                    pass
                else:
                    self.outstanding_stock_dict[order_number] = {}

                self.outstanding_stock_dict[order_number].update({"종목코드": stock_code})
                self.outstanding_stock_dict[order_number].update({"종목명": stock_name})
                self.outstanding_stock_dict[order_number].update({"주문번호": order_number})
                self.outstanding_stock_dict[order_number].update({"주문상태": order_status})
                self.outstanding_stock_dict[order_number].update({"주문수량": order_quantity})
                self.outstanding_stock_dict[order_number].update({"주문가격": order_price})
                self.outstanding_stock_dict[order_number].update({"주문구분": order_type})
                self.outstanding_stock_dict[order_number].update({"미체결수량": outstanding_quantity})
                self.outstanding_stock_dict[order_number].update({"체결량": conclusion_quantity})

                print(">> self.outstanding_stock_dict: %s" % self.outstanding_stock_dict)
        
        self.disconnect_screen_number(self.screen_number_account)
        self.event_loop_tr_data.exit()
        print(">>> function[slot_tr_data] end <<<")

    def slot_real_data(self, stock_code, real_type, real_data):
#         print("")
#         print(">>> function[slot_real_data] start >>>")
#         print(">> stock_code: %s" % stock_code)
#         print(">> real_type: %s" % real_type)
#         print(">> real_data %s" % real_data)

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
                    self.dynamicCall("SetRealRemove(QString, QString)", self.portfolio_stock_dict[code]["스크린번호"], code)
                    print(">> 종목코드[%s] 실시간 연결 종료." % code)

                # 다음 날을 위한 종목분석 시작
                QTest.qWait(5000)
                # self.file_delete() # 초기화(포트폴리오) 파일삭제 또는 디비 삭제
                # self.calculate_fnc() # 종목분석(알고리즘 적용) 후 파일 또는 디비 저장

                # 프로그램 종료
                sys.exit()
                
            print(">> market_op_type: %s" % market_op_type)
            print(">> conclusion_time: %s" % str(datetime.timedelta(conclusion_time)))
            print(">> market_open_remain_time %s" % str(datetime.timedelta(market_open_remain_time)))

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

            # 스크리닝 종목 데이터를 포트폴리오 딕셔너리에 업데이트
            if stock_code not in self.portfolio_stock_dict:
                self.portfolio_stock_dict.update({stock_code: {}})

            self.portfolio_stock_dict[stock_code].update({"체결시간": conclusion_time})
            self.portfolio_stock_dict[stock_code].update({"현재가": close_price})
            self.portfolio_stock_dict[stock_code].update({"전일대비": net_change})
            self.portfolio_stock_dict[stock_code].update({"등락율": fluctuation_rate})
            self.portfolio_stock_dict[stock_code].update({"(최우선)매도호가": first_ask_price})
            self.portfolio_stock_dict[stock_code].update({"(최우선)매수호가": first_bid_price})
            self.portfolio_stock_dict[stock_code].update({"거래량": volume})
            self.portfolio_stock_dict[stock_code].update({"누적거래량": cumulative_volume})
            self.portfolio_stock_dict[stock_code].update({"고가": high_price})
            self.portfolio_stock_dict[stock_code].update({"시가": open_price})
            self.portfolio_stock_dict[stock_code].update({"저가": low_price})

            # (매도)계좌평가잔고내역의 보유 종목
            # 실시간 반영되지 않기 때문에 일회성으로 사용하고 더 이상 사용하지 않는다.
            # 종목이 딕셔너리에 있는지 확인하고 매매가능수량을 체크해서 매도주문한다.
            # 실시간 매수가 없어야 하므로 self.balance_stock_dict에 미존재여야 한다.
            if stock_code in self.account_stock_dict.keys() and stock_code not in self.balance_stock_dict.keys():
                account = self.account_stock_dict[stock_code]
                profit_loss_rate = (close_price - account["매입가"]) / account["매입가"] * 100

                if account["매매가능수량"] > 0 and profit_loss_rate > 2:
                    order_success = self.dynamicCall(
                        "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                        ["신규매도", self.portfolio_stock_dict[stock_code]["주문용스크린번호"],
                        self.account_number, 2, stock_code, account["매매가능수량"], 0, "03", ""
                        ]
                    )

                    if order_success == 0:
                        print(">> [계좌평가잔고내역]매도주문 전달 성공[%s]" % order_success)
                        del self.account_stock_dict[stock_code]
                        print(">> self.account_stock_dict: %s" % self.account_stock_dict)
                    else:
                        print(">> [계좌평가잔고내역]매도주문 전달 실패[%s]" % order_success)

            # (매도) 실시간 매수 종목
            # 수익률: (현재가-매입단가)/매입단가*100 (10000-9500)/9500*100
            elif stock_code in self.balance_stock_dict.keys():
                balance = self.balance_stock_dict[stock_code]

                # 수익률 계산
                profit_loss_rate = (close_price - balance["매입단가"]) / balance["매입단가"] * 100

                # 매도조건: 주문가능수량이 있고 수익률이 +-5 범위라면 익절 또는 손절한다.
                if balance["주문가능수량"] > 0 and (profit_loss_rate > 2 or profit_loss_rate < -2):
                    order_success = self.dynamicCall(
                        "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                        ["신규매도", self.portfolio_stock_dict[stock_code]["주문용스크린번호"],
                         self.account_number, 2, stock_code, balance["주문가능수량"], 0, "03", ""
                         ]
                    )

                    if order_success == 0:
                        print(">> [실시간매수종목]매도주문 전달 성공[%s]" % order_success)
                    else:
                        print(">> [실시간매수종목]매도주문 전달 실패[%s]" % order_success)

            # 종목 정보를 실시간으로 받는 도중 조건에 일치하면 매수 매도 주문을 넣는다.
            # 등락율이 2.0 이상이면 매수하도록 구성. 실시간 계좌 데이터 딕셔너리 미존재.
            # balance_stock_dict : 매수된 종목 관리, 매수된 종목은 매도해야한다. 매도주문.
            elif fluctuation_rate > 8.0 and stock_code not in self.balance_stock_dict:
                print(">> 매수조건 통과: %s" % stock_code)
                print(">> 예수금 체크: %s" % self.deposit)

                # 예수금의 10%만 사용하도록 한다. 비율은 추후 조정.
                result = (self.deposit * 0.1) / first_ask_price
                quantity = int(result)

                print(">> 매수 가능 주식수: %s" % quantity)
                
                if quantity < 10:
                    pass

                # 매수 요청 (사용자구분명, 화면번호, 계좌번호, 주문유형, 종목코드, 주문수량, 주문가격, 거래구분, 원주문번호)
                order_success = self.dynamicCall(
                    "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                    ["신규매수",
                     self.portfolio_stock_dict[stock_code]["주문용스크린번호"],
                     self.account_number,
                     1, stock_code, quantity, first_ask_price, "00", ""]
                )

                if order_success == 0:
                    print(">> 매수주문 전달 [%s]성공: %s" % (order_success, stock_code))
                else:
                    print(">> 매수주문 전달 [%s]실패: %s" % (order_success, stock_code))

                # 미체결 수량 매수 취소 (주문번호만 뽑아 리스트로 만든다)
                outstanding_list = list(self.outstanding_stock_dict)
                print(">> 미체결 주문 %s건 존재." % len(outstanding_list))
                for order_number in outstanding_list:
                    print(">> order_number: %s" % order_number)

                    # 종목코드, 주문가격, 미체결수량, 주문구분
                    a = self.outstanding_stock_dict[order_number]["종목코드"]
                    b = int(self.outstanding_stock_dict[order_number]["주문가격"])
                    c = int(self.outstanding_stock_dict[order_number]["미체결수량"])
                    d = self.outstanding_stock_dict[order_number]["주문구분"].lstrip("+").lstrip("-")
                    
                    print("")
                    print(">> 종목코드(a): [%s]" % a)
                    print(">> 주문가격(b): [%s]" % b)
                    print(">> 미체결수량(c): [%s]" % c)
                    print(">> 주문구분(d): [%s]" % d)

                    if d == "매수" and c > 0 and first_ask_price > b:
                        order_success = self.dynamicCall(
                            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                            ["매수취소", self.portfolio_stock_dict[stock_code]["주문용스크린번호"],
                             self.account_number, 3, a, 0, 0, "00", order_number
                             ]
                        )

                        if order_success == 0:
                            print(">> 매수취소 전달 [%s]성공: %s" % (order_success, a))
                        else:
                            print(">> 매수취소 전달 [%s]실패: %s" % (order_success, a))

                    elif c == 0:
                        del self.outstanding_stock_dict[order_number]
                        print(">> 체결된(미체결수량:0) 주문번호[%s] 삭제" % order_number)

        self.disconnect_screen_number(self.screen_number_market)
        self.event_loop_real_data.exit()

    """
          [OnReceiveChejanData() 이벤트]
          
          OnReceiveChejanData(
          BSTR sGubun, // 체결구분: 접수와 체결시 '0'값, 국내주식 잔고전달은 '1'값, 파생잔고 전달은 '4'
          LONG nItemCnt, (미사용)
          BSTR sFIdList (미사용)
          )
          
          주문요청후 주문접수, 체결통보, 잔고통보를 수신할 때 마다 호출되며 GetChejanData()함수를 이용해서 상세한 정보를 얻을수 있습니다.    
    """
    def slot_chejan_data(self, conclusion_type, item_cnt, fid_list):
#         print("")
#         print(">> 체결구분: %s" % conclusion_type)
#         print(">> 항목건수: %s" % item_cnt)
#         print(">> FID 목록: %s" % fid_list)

        conclusion_type = int(conclusion_type)

        # 0:주문체결, 1:잔고
        """
            Real Type : 주문체결
            [9201] = 계좌번호
            [9203] = 주문번호
            [9205] = 관리자사번
            [9001] = 종목코드,업종코드
            [912] = 주문업무분류
            [913] = 주문상태
            [302] = 종목명
            [900] = 주문수량
            [901] = 주문가격
            [902] = 미체결수량
            [903] = 체결누계금액
            [904] = 원주문번호
            [905] = 주문구분
            [906] = 매매구분
            [907] = 매도수구분
            [908] = 주문/체결시간
            [909] = 체결번호
            [910] = 체결가
            [911] = 체결량
            [10] = 현재가
            [27] = (최우선)매도호가
            [28] = (최우선)매수호가
            [914] = 단위체결가
            [915] = 단위체결량
            [938] = 당일매매수수료
            [939] = 당일매매세금
            [919] = 거부사유
            [920] = 화면번호
            [921] = 터미널번호
            [922] = 신용구분(실시간 체결용)
            [923] = 대출일(실시간 체결용)        
        """
        if conclusion_type == 0:    # 주문체결
            account_number = self.dynamicCall("GetChejanData(int)", 9201)
            stock_code = self.dynamicCall("GetChejanData(int)", 9001)[1:]
            stock_name = self.dynamicCall("GetChejanData(int)", 302).strip()
            origin_order_number = self.dynamicCall("GetChejanData(int)", 904)
            order_number = self.dynamicCall("GetChejanData(int)", 9203)
            order_status = self.dynamicCall("GetChejanData(int)", 913)
            order_quantity = int(self.dynamicCall("GetChejanData(int)", 900))
            order_price = int(self.dynamicCall("GetChejanData(int)", 901))
            outstanding_quantity = int(self.dynamicCall("GetChejanData(int)", 902))
            order_type = self.dynamicCall("GetChejanData(int)", 905).strip().lstrip("+").lstrip("-")
            order_conclusion_time = self.dynamicCall("GetChejanData(int)", 908)
            conclusion_price = self.dynamicCall("GetChejanData(int)", 910).strip()
            conclusion_quantity = self.dynamicCall("GetChejanData(int)", 911).strip()
            close_price = int(self.dynamicCall("GetChejanData(int)", 10))
            first_ask_price = int(self.dynamicCall("GetChejanData(int)", 27))
            first_bid_price = int(self.dynamicCall("GetChejanData(int)", 28))
            
            if conclusion_price == '': conclusion_price = "0"
            if conclusion_quantity == '': conclusion_quantity = "0"
            
            conclusion_price = int(conclusion_price)    
            conclusion_quantity = int(conclusion_quantity)

            # 신규 주문이면 미체결 딕셔너리에 주문번호 할당
            if order_number not in self.outstanding_stock_dict.keys():
                self.outstanding_stock_dict.update({order_number: {}})

            self.outstanding_stock_dict[order_number].update({"종목코드": stock_code})
            self.outstanding_stock_dict[order_number].update({"주문번호": order_number})
            self.outstanding_stock_dict[order_number].update({"종목명": stock_name})
            self.outstanding_stock_dict[order_number].update({"주문상태": order_status})
            self.outstanding_stock_dict[order_number].update({"주문수량": order_quantity})
            self.outstanding_stock_dict[order_number].update({"주문가격": order_price})
            self.outstanding_stock_dict[order_number].update({"미체결수량": outstanding_quantity})
            self.outstanding_stock_dict[order_number].update({"원주문번호": origin_order_number})
            self.outstanding_stock_dict[order_number].update({"주문구분": order_type})
            self.outstanding_stock_dict[order_number].update({"주문/체결시간": order_conclusion_time})
            self.outstanding_stock_dict[order_number].update({"체결가": conclusion_price})
            self.outstanding_stock_dict[order_number].update({"체결량": conclusion_quantity})
            self.outstanding_stock_dict[order_number].update({"현재가": close_price})
            self.outstanding_stock_dict[order_number].update({"(최우선)매도호가": first_ask_price})
            self.outstanding_stock_dict[order_number].update({"(최우선)매수호가": first_bid_price})
            print(">> self.outstanding_stock_dict: %s" % self.outstanding_stock_dict)

        elif conclusion_type == 1:  # 잔고
            account_number = self.dynamicCall("GetChejanData(int)", 9201)
            stock_code = self.dynamicCall("GetChejanData(int)", 9001)[1:]
            stock_name = self.dynamicCall("GetChejanData(int)", 302).strip()
            close_price = abs(int(self.dynamicCall("GetChejanData(int)", 10)))
            retention_quantity = int(self.dynamicCall("GetChejanData(int)", 930))
            orderable_quantity = int(self.dynamicCall("GetChejanData(int)", 933))
            purchase_price = int(self.dynamicCall("GetChejanData(int)", 931))
            total_purchase_price = int(self.dynamicCall("GetChejanData(int)", 932))
            sell_buy_type = self.dynamicCall("GetChejanData(int)", 946).strip()
            first_ask_price = int(self.dynamicCall("GetChejanData(int)", 27))
            first_bid_price = int(self.dynamicCall("GetChejanData(int)", 28))

            if stock_code not in self.balance_stock_dict.keys():
                self.balance_stock_dict.update({stock_code: {}})

            self.balance_stock_dict[stock_code].update({"현재가": close_price})
            self.balance_stock_dict[stock_code].update({"종목코드": stock_code})
            self.balance_stock_dict[stock_code].update({"종목명": stock_name})
            self.balance_stock_dict[stock_code].update({"보유수량": retention_quantity})
            self.balance_stock_dict[stock_code].update({"주문가능수량": orderable_quantity})
            self.balance_stock_dict[stock_code].update({"매입단가": purchase_price})
            self.balance_stock_dict[stock_code].update({"총매입가": total_purchase_price})
            self.balance_stock_dict[stock_code].update({"매도/매수구분": sell_buy_type})
            self.balance_stock_dict[stock_code].update({"(최우선)매도호가": first_ask_price})
            self.balance_stock_dict[stock_code].update({"(최우선)매수호가": first_bid_price})
            print(">> self.balance_stock_dict: %s" % self.balance_stock_dict)

            if retention_quantity == 0:
                del self.balance_stock_dict[stock_code]
                print(">> after del > self.balance_stock_dict: %s" % self.balance_stock_dict)

    def merge_stock_dict(self):
        print("")
        self.all_stock_dict.update({"계좌평가잔고내역": self.account_stock_dict})
        self.all_stock_dict.update({"미체결종목": self.outstanding_stock_dict})
        self.all_stock_dict.update({"포트폴리오종목": self.portfolio_stock_dict})
        print(">> all_stock_dict{}: %s" % self.all_stock_dict)
        print("")

    def set_screen_number(self):

        self.merge_stock_dict()
        screen_overwrite = []

        # 계좌평가잔고내역 종목
        for stock_code in self.account_stock_dict.keys():
            if stock_code not in screen_overwrite:
                screen_overwrite.append(stock_code)

        # 미체결종목
        for order_number in self.outstanding_stock_dict.keys():
            stock_code = self.outstanding_stock_dict[order_number]["종목코드"]
            if stock_code not in screen_overwrite:
                screen_overwrite.append(stock_code)

        # 포트폴리오 종목
        for stock_code in self.portfolio_stock_dict.keys():
            if stock_code not in screen_overwrite:
                screen_overwrite.append(stock_code)

#         print(">> 스크린번호 리스트에 종목코드 %s건 통합 완료" % len(screen_overwrite))
#         print(">> 스크린번호 할당 시작")

        cnt = 0
        for stock_code in screen_overwrite:
            screen_number_stock = int(self.screen_number_stock)
            screen_number_order = int(self.screen_number_order)

#             print(">> 주식용 스크린번호: %s" % screen_number_stock)
#             print(">> 주문용 스크린번호: %s" % screen_number_order)

            if (cnt % 50) == 0:
                screen_number_stock += 1
                screen_number_order += 1
                self.screen_number_stock = str(screen_number_stock)
                self.screen_number_order = str(screen_number_order)

            # 모든 스크린 번호는 포트폴리오 딕셔너리에 추가. 변하는 종목의 데이터 보과 및 업데이트 용도.
            if stock_code in self.portfolio_stock_dict.keys():
                self.portfolio_stock_dict[stock_code].update({"스크린번호": self.screen_number_stock})
                self.portfolio_stock_dict[stock_code].update({"주문용스크린번호": self.screen_number_order})
            elif stock_code not in self.portfolio_stock_dict.keys():
                print(">> stock_code[%s] not in self.portfolio_stock_dict: " % stock_code)
                self.portfolio_stock_dict.update(
                    {stock_code: {"스크린번호": self.screen_number_stock, "주문용스크린번호": self.screen_number_order}})

            cnt += 1

#         print(">> portfolio_stock_dict{}: %s" % self.portfolio_stock_dict)
        print(">> 스크린번호 %s건 할당 완료" % cnt)

    # 대상 종목(보유,미체결,포트폴리오) 실시간 등록
    def all_stock_real_reg(self):
        for stock_code in self.portfolio_stock_dict.keys():
            screen_number = self.portfolio_stock_dict[stock_code]["스크린번호"]
            fids = "20;10;12;15;16;17;18"
            self.dynamicCall("SetRealReg(QString, QString, QString, QString)", screen_number, stock_code, fids, "1")

    def slot_msg(self, screen_number, rq_name, tr_code, msg):
#         print("")
        print("> screen_number: %s, rq_name: %s, tr_code: %s, msg: %s," % (screen_number, rq_name, tr_code, msg))

    def disconnect_screen_number(self, screen_number=None):
        self.dynamicCall("DisconnectRealData(QString)", screen_number)
#         print(">>> The number[%s] of screen disconnected." % screen_number)
