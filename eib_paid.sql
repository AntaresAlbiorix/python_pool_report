select   plst.pool_id
       , olst.STATUS 
       , to_char(nvl(os.sum_cur*exr.rate,0), '999,999,990.99') settle_rur
       , to_char(NVL(zhu.eib,0), '999,999,990.99') eib_all
       , to_char(NVL(zhu.eib4,0), '999,999,990.99') eib_nonlapse
       , to_char(zhu.bonus_paid+zhu.bonus_ocr, '999,999,990.99') bonus_claimed
  
  from life2makc.pool_list plst
  
  join life2makc.rf_option_list olst
    on olst.strategy_id = plst.strategy_id
   and plst.hist_stage = olst.hist_stage
  
  join life2makc.rf_option_settlement os
    on os.option_id=olst.option_id
  
  left join lifemakc.rate exr
     on exr.currency = 'USD'
    and exr.rate_date = olst.invest_end_date
    
  left join ( select   sum(nvl(t.bonus_paid,0)) bonus_paid, sum(nvl(t.bonus_ocr,0)) bonus_ocr, sum(nvl(e.bonus,0)) eib, sum(case when d.status = 4 then nvl(e.bonus,0) end) eib4, p.pool_id 
              from lifemakc.dogovor d 
                left join  life2makc.zhu4eib t                                   --вьюшка из актуального ЖУ 
                 on d.contract_id = t.cid
                left join life2makc.policy_ku_4_budget_ver_tab v
                 on d.contract_id = v.contract_id  
                left join life2makc.cls_invest_details p 
                 on p.product_key=v.product_key
                and p.product_ver=v.product_ver
                left join life2makc.eib_withdeaths e
                on e.contract_id = d.contract_id
              where 1=1 
               and d.program_type in ('isz', 'disz')
              group by  p.pool_id   order by  p.pool_id                                      	
            ) zhu
   on zhu.pool_id = plst.pool_id
      
where plst.strategy_id in ({strat})
   and trim(olst.invest_start_date) in ({optdate}) 
 order by plst.pool_id  
