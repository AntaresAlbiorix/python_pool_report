
-------------убрать из расчета средневзвешенного  ” договоры MKX--------------------------------------------------------------------------------------------
-------------добавить скидку на cool-off (в текущей версии дл€ сверки с Excel необходимо сперва занулить ее на листе contents коэфом)-----------------------

select  --*
       q.pool_id
     , q.program_market   
     , q.date_option                                                                       
     , q.rate
     , round(q.AVG_KU,6)*100   AVG_KU
     , q.nominal
     , p.face_value 
     , round(p.face_value-q.nominal,2)  leftover                                               --остаток по текущему пулу  
     , case when q.strategy_id in (3,8) then 0 
                                        else nvl(LAG(round(p.face_value_acc-q.nominal_acc,2)) OVER(partition by p.strategy_id order by p.hist_stage) ,0)
       end       
              prev_pool                                                                       --хвост от предыдущего пула
     
     , round(  case when q.strategy_id in (3,8) then (p.face_value-q.nominal)
                                                else (p.face_value_acc-q.nominal_acc)
                end                                  
         ,2)    
              total_leftover                                                                  --остаток номинала с учетом хвоста
     
     , round(  case when q.strategy_id in (3,8) then (p.face_value-q.nominal)
                                                else (p.face_value_acc-q.nominal_acc)
                end                                  
              /  q.avg_ku*q.rate 
         ,2)    
               LEFT_PREM                                                                      -- лимит продаж (руб)

from
  (  select  --сумма номинала, средневзвеш.  ” в разрезе pool_id
           distinct  dog.pool_id  ,  dog.program_market, dog.date_option, dog.strategy_id, dog.hist_stage
                   ,  MAX(dog.RATE)  over (partition by dog.pool_id ) rate
                   ,  1/sum(avg_ku) over (partition by dog.pool_id ) AVG_KU --средневзвешенный  ” по pool_id
                   ,  sum(dog.nominal) over (partition by dog.pool_id ) NOMINAL --израсходованный номинал по пулу
                   ,  sum(dog.nominal) over (partition by dog.strategy_id order by  dog.hist_stage range UNBOUNDED PRECEDING) NOMINAL_acc --израсходованный номинал по пулу накопленным итогом 
                     
           from (    
                      --расчет номинала и дол€ в 1/ср. ” подоговорно, с прив€зкой к strat_id и pool_id
                select
                       inv.pool_id, p.strategy_id, p.hist_stage,  d.date_option, d.program_market, R.RATE
                     , (d.premia_val* (case when lower(d.currency)='rur' then 1 else r.rate end)/r.rate) --* (case when d.bank='MKX' then 0 else 1 end)
                        /
                        sum( (d.premia_val * (case when p.strategy_id in (3,8) then round(nvl(d.coupon_profit,0)/(case when p.strategy_id=3 then 8 else 11 end)  ,4)
                                                else nvl(d.particion_coef,0)/100
                                                end)  -- ”
                                          * (case when lower(d.currency)='rur' then 1 else r.rate end)/r.rate) --курс валюты
                            ) over (partition by inv.pool_id)
                                          
                                              avg_ku         
                                                
                     ,  (d.premia_val * (case when p.strategy_id in (3,8) then round(nvl(d.coupon_profit,0)/(case when p.strategy_id=3 then 8 else 11 end)  ,4)
                                                else nvl(d.particion_coef,0)/100
                                                end)
                                          * (case when lower(d.currency)='rur' then 1 else r.rate end)/r.rate)  NOMINAL
                                         
                from lifemakc.dogovor d
                  cross join (select max(r.rate_date) mrd from lifemakc.rate r where r.currency='USD' and r.rate_date> to_date('01/03/2017', 'dd/mm/yyyy'))
                  join (select r.* from lifemakc.rate r
                               where r.currency='USD'
                               and r.rate_date> to_date('01/03/2017', 'dd/mm/yyyy')
                       ) r
                  on r.rate_date = least ( mrd ,  d.date_option  )

                  join life2makc.policy_ku_4_budget_ver_tab k
                                on k.contract_id=d.contract_id
                  join lifemakc.cls_invest_details inv
                                on inv.product_key=k.product_key
                                and inv.product_ver=k.product_ver
                  join life2makc.pool_list p
                                on inv.pool_id=p.pool_id
                  where 1=1 and d.status in (0,1,7,6,4,14)  
                            and d.program_type in ('isz')    
                
               ) dog 
   )q 
        
join  
   ( select ot.pool_id, ot.strategy_id, ot.hist_stage
                       , sum(ot.transaction_face_value) over (partition by ot.strategy_id, ot.hist_stage) face_value
                       , sum(ot.transaction_face_value) over (partition by ot.strategy_id order by ot.hist_stage rows UNBOUNDED PRECEDING ) face_value_acc --купленный номинал на пул
       from --купленный номинал по каждому pool_id
        (   select   pz.pool_id, nvl(pz.strategy_id,-1)strategy_id, nvl(pz.hist_stage,-1)hist_stage, sum(nvl(ot.transaction_face_value,0)) transaction_face_value   --купленный номинал накопленным итогом     
              from    life2makc.pool_list pz
              left join life2makc.rf_option_list ol
                   on  ol.strategy_id=pz.strategy_id
                   and ol.hist_stage = pz.hist_stage
              left join life2makc.rf_option_transactions ot
                   on ot.option_id=ol.option_id
             group by pz.pool_id , pz.strategy_id, pz.hist_stage
        )ot
    )p     
on  p.pool_id=q.pool_id

where 1=1
--and q.strategy_id=9 
and q.DATE_OPTION = to_date('26/09/2019', 'dd/mm/yyyy') 
order by p.pool_id
;
