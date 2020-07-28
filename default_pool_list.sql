select   distinct
     inv.pool_id pool_id
  ,  inv.strategy_id   strategy_id
  ,  to_char(t.date_option) date_opt
from lifemakc.dogovor t 
join life2makc.policy_ku_4_budget_ver_tab v
     on v.contract_id=t.contract_id
join life2makc.cls_invest_details inv
     on inv.product_key=v.product_key
     and inv.product_ver = v.product_ver       
where 1=1 
and t.status in (0,1,7,3,6,4)
and t.begin_date >= (sysdate-30)
order by 1
