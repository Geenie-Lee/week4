drop table public.coin_market cascade;

create table public.coin_market (
	market varchar(50) not null,
	korean_name varchar(50) not null,
	english_name varchar(50) not null,
	market_warning varchar(100),
	dt varchar(8) not null default to_char(current_date,'yyyymmdd')
);

create unique index coin_market_ix on public.coin_market using btree (market,korean_name,english_name);
