drop table public.stock_rtm_cfreq cascade;

create table public.stock_rtm_cfreq (
	stock_code varchar(20) not null,
	dt varchar(8) not null,
	tm varchar(4) not null,
	price int4 not null default 0,
	volume int4 not null default 0,
	freq  int4 not null default 0,
	iscur varchar(1) not null default 'N',
	isbuy varchar(1) not null default 'N'
);

alter table stock_rtm_cfreq add column max_volume int4;

create unique index stock_rtm_cfreq_uk on public.stock_rtm_cfreq using btree (stock_code,price,dt desc);


select volume,freq from stock_rtm_cfreq where dt = to_char(current_date,'yyyymmdd') and stock_code = ? and price = ?

stock_code,dt,tm,price,volume,freq,iscur


update stock_rtm_cfreq set volume = %s, freq = %s where dt = to_char(current_date,'yyyymmdd') and stock_code = ? and price = ?



select * from stock_rtm_cfreq where dt = to_char(current_date,'yyyymmdd') order by stock_code, tm desc;