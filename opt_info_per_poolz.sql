select plst.pool_id,
       to_char(round(str.coupon, 0)) coupon,
	   olst.isin,
       to_char(otrs.transaction_date) transaction_date,
       otrs.option_price,
       to_char(nvl(oclc.reporting_date, oclc.valuation_date)) calc_date,
       oclc.bs_value,
       otrs.transaction_face_value fv_usd,
       to_char(olst.invest_start_date) invest_start_date,
       to_char(olst.invest_end_date) invest_end_date
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
  join life2makc.cls_strategy_ref str
    on str.strategy_id = olst.strategy_id
 where plst.strategy_id in ({strat})
   and olst.invest_start_date in ({optdate}) 
 order by plst.pool_id  