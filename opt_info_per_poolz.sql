select plst.pool_id,
       olst.status,
       --to_char(round(str.coupon, 0)) coupon,        --флаг для особой обработки купонников
	   olst.isin,
       to_char(otrs.transaction_date) transaction_date,
       to_char(round(otrs.option_price*100,3)||'%') option_price,
       to_char(nvl(oclc.reporting_date, oclc.valuation_date)) calc_date,
       to_char(round(oclc.bs_value*100,3)||'%') bs_value,
       to_char(otrs.transaction_face_value, '999,999,990.99') fv_usd,
       to_char(olst.invest_start_date) invest_start_date,
       to_char(olst.invest_end_date) invest_end_date,
       to_char(nvl(os.sum_cur,0), '999,999,990.99') sum_cur
  from life2makc.rf_option_list olst
  join life2makc.pool_list plst
    on olst.strategy_id = plst.strategy_id
   and plst.hist_stage = olst.hist_stage
  left join life2makc.rf_option_transactions otrs
    on otrs.option_id = olst.option_id
  left join (select oclc.*,
                    rank() over(partition by oclc.option_id order by oclc.valuation_date desc) rnk
               from life2makc.rf_option_calc oclc) oclc
    on oclc.option_id = olst.option_id
   and oclc.rnk = 1
  left join life2makc.rf_option_settlement os
       on os.option_id=olst.option_id   
  --join life2makc.cls_strategy_ref str
  --  on str.strategy_id = olst.strategy_id
  where plst.strategy_id in ({strat})
   and trim(plst.date_option) in ({optdate})
 order by plst.pool_id , otrs.transaction_date
