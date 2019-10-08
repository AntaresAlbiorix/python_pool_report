select  to_char(t.date_option)
from ( select distinct t.date_option from life2makc.pool_list t
where t.strategy_id in ({strat})
order by t.date_option )t