select 
	p.pool_id pool_id
  ,	p.strategy_id 	strategy_id
  , to_char(p.date_option) date_opt
from lifemakc.date_option t 
left join life2makc.pool_list p
  on p.date_option=t.date_opt
  and p.program_market=t.program
  and p.term=t.kol_year
where 1=1 
and t.inforce=1
and upper(t.bank) not in 'TST' 
group by    p.pool_id, 
  p.strategy_id, p.date_option
order by 1