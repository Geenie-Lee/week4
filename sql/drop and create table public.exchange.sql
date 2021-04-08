drop table public.exchange cascade;

create table public.exchange (
	dt varchar(8)  not null default to_char(current_date,'yyyymmdd'),
	tm varchar(4) not null,
	currency varchar(20) not null,
	price varchar(20) not null default '0',
	freq  int4 not null default 0,
	iscur varchar(1)
);
  