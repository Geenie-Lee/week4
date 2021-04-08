-------------------------------------------------------------------------------
-- (변동성 돌파 전략) 당일자 고가와 저가의 갭이 10프로 이상인 종목 중에서 선택
-------------------------------------------------------------------------------

select stock_code
     , hl_gap_price
     , stock_name
  from 
     (
		select stock_code
		     , stock_name
		     , market_type 
		     , volume 
		     , trading_value 
		     , open_price 
		     , high_price 
		     , low_price 
		     , close_price 
		     , high_price-low_price as hl_gap_price
		     , round(((high_price-low_price)::float/close_price::float)*100) as hl_gap_rate
		  from stock_day_kospi
		 where day_num = 1     
     ) a
 where 1=1
   and a.hl_gap_rate between 15 and 25
 order by stock_name ;



select stock_code
     , hl_gap_price
     , stock_name
  from 
     (
		select stock_code
		     , stock_name
		     , market_type 
		     , volume 
		     , trading_value 
		     , open_price 
		     , high_price 
		     , low_price 
		     , close_price 
		     , high_price-low_price as hl_gap_price
		     , round(((high_price-low_price)::float/close_price::float)*100) as hl_gap_rate
		  from stock_day_kosdaq
		 where day_num = 1     
     ) a
 where 1=1
   and a.hl_gap_rate between 15 and 25
 order by stock_name ;