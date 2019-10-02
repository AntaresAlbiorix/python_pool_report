
-------------убрать из расчета средневзвешенного КУ договоры MKX--------------------------------------------------------------------------------------------
-------------добавить скидку на cool-off (в текущей версии для сверки с Excel необходимо сперва занулить ее на листе contents коэфом)-----------------------

select  --*
       q.pool_id
     , q.program_market   
     , q.date_option                                                                       
     , q.rate
     , round(q.AVG_KU,6)*100   AVG_KU
     , q.nominal
     , p.face_value 
     , round(p.face_value-q.nominal,2)  leftover                                               --остаток по текущему пулу  
     , case when q.is_coupon =1 then 0 
                                else nvl(LAG(round(p.face_value_acc-q.nominal_acc,2)) OVER(partition by p.strategy_id order by p.hist_stage) ,0)
       end       
              prev_pool                                                                       --хвост от предыдущего пула
     
     , round(  case when q.is_coupon =1 then (p.face_value-q.nominal)
                                        else (p.face_value_acc-q.nominal_acc)
                end                                  
         ,2)    
              total_leftover                                                                  --остаток номинала с учетом хвоста
     
     , round(  case when q.is_coupon =1 then (p.face_value-q.nominal)
                                        else (p.face_value_acc-q.nominal_acc)
                end                                  
              /  q.avg_ku*q.rate 
         ,2)    
               LEFT_PREM                                                                      -- лимит продаж (руб)

from
  --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  -- Q - > Все пулы с признаками, необходимыми для расчета остатка
  --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  (  select  --сумма номинала, средневзвеш. КУ в разрезе pool_id
            
           -- ! Поменять distinct на group by
           distinct  
                  dog.pool_id
               ,  dog.program_market  -- маркетинговое название стратегии
               ,  dog.date_option
               ,  dog.strategy_id
               ,  dog.hist_stage
               ,  dog.is_coupon
                  
                   -- ? Зачем максимум, если только 1 курс для пула ?
                   ,  MAX(dog.RATE)  over (partition by dog.pool_id ) rate                   
                   
                   ,  1/sum(avg_ku) over (partition by dog.pool_id ) AVG_KU --средневзвешенный КУ по pool_id
                   
                   ,  sum(dog.nominal) over (partition by dog.pool_id ) NOMINAL --израсходованный номинал по пулу
                   ,  sum(dog.nominal) over (partition by dog.strategy_id order by  dog.hist_stage range UNBOUNDED PRECEDING) NOMINAL_acc --израсходованный номинал по пулу накопленным итогом 
                     
           from 
           --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
           -- DOG - > Все договоры с признаками, необходимыми для расчета остатка
           --         расчет номинала и доля в 1/ср.КУ подоговорно, с привязкой к strat_id и pool_id
           --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
           (                         
                select 
                         inv.pool_id
                       , p.strategy_id
                       , p.hist_stage
                       , p.coupon as is_coupon
                       , d.date_option
                       , d.program_market
                       , R.RATE
                                    
                      , -- Вклад каждого полиса в ( 1 / [средневзвешенный КУ]). Сумма этих показателей по пулу дает 1 / [средневзвешенный КУ] по пулу
                        -- Тоже самое, что Вклад каждого полиса в [средневзвешенный КУ]
                        -- SUMj( Gj x Фj / SUMi(Gi)) [=средневзвеш КУ] = 1 / SUMj( Gj / SUMi(Gi x Фi)) [рассчитывается в запросе]
                        
                        -- [1. Премия в валюте] / [ 2. Номинал по пулу]
                        /* 1 */ (d.premia_val * (case when lower(d.currency)='rur' then 1/r.rate else 1 end))                 --* (case when d.bank='MKX' then 0 else 1 end)
                                 /
                        /* 2 */ sum( (d.premia_val * (case when p.coupon=1 then round(nvl(d.coupon_profit/100,0)/p.coupon_rate,4)
                                                else nvl(d.particion_coef,0)/100
                                                end)  --КУ
                                          * (case when lower(d.currency)='rur' then 1/r.rate else 1 end)) --курс валюты
                            ) over (partition by inv.pool_id)
                                          
                            -- ? почему название avg_ku, когда рассчитывается (1 / avg_ku)  ?                            
                                              avg_ku

                      
                     ,  -- Израсходованный номинал в валюте
                        -- ? Переделать соотв расчет для памятки ?
                        -- ? Убрать округление 4 ?
                         (d.premia_val * (case when p.coupon =1 then round(nvl(d.coupon_profit/100,0)/p.coupon_rate,4) 
                                                else nvl(d.particion_coef,0)/100
                                                end)
                                          * (case when lower(d.currency)='rur' then 1/r.rate else 1 end))  NOMINAL  
                                         
                from lifemakc.dogovor d
                  -- Последняя доступная дата, на которую есть курс
                  cross join (select max(r.rate_date) mrd from lifemakc.rate r where r.currency='USD' and r.rate_date> to_date('01/03/2017', 'dd/mm/yyyy') /* уменьшение объема выборки */)                  

                  left join
                  -- Курсы на мин дату: опциона, последнюю доступную. 
                  -- Риск: нет курса на дату опциона (обоснованный риск) -> не будет расчета  
                  -- Создать поле с контролем ошибок?
                  lifemakc.rate r
                  on r.rate_date = least(mrd,  d.date_option  )
                  
                  -- Связь со справочниками CLS
                  -- !? Поменять на cid_keyver
                  join life2makc.policy_ku_4_budget_ver_tab k
                  --join lifemakc.cid_keyver k
                                on k.contract_id=d.contract_id

                  -- ИД пула
                  join lifemakc.cls_invest_details inv
                                on inv.product_key=k.product_key
                                and inv.product_ver=k.product_ver
                  
                  -- Стратегия, hist_stage (Номер пула в рамках стратегии), идентификатор того, является ли стратегия купонной, купонная ставка
                  join (
                         select  p.pool_id
                               , p.strategy_id
                               , p.hist_stage
                               , sr.coupon
                               , case when sr.coupon=1 then nvl( l.coupon_rate,  LAG (l.coupon_rate) OVER (partition by p.strategy_id order by p.hist_stage))
                                    else -1
                                 end as coupon_rate
                          from life2makc.pool_list p
                                                 
                          --Справочник стратегий, чтобы определить является ли стратегия купонной, нужно ли по ней подтягивать ставку купона из option_list для расчета КУ                 
                          join life2makc.cls_strategy_ref sr 
                                        on sr.strategy_id = p.strategy_id

                          --Список опционов для того, чтобы получить ставку купона по купленным активам, для расчета КУ по купонникам
                          --left join т.к. могут быть пулы, по которым не куплен опцион (e.g. пул#51 - в pool_list есть hist_stage=1, а в option_list начинается с 2). т.е. если будет купонник с подобным раскладом, то по нему  не подтянется КУ, т.к. не будет соответствующей бумаги.  
                          left join (select l.strategy_id, l.hist_stage, max (l.coupon_rate) coupon_rate from life2makc.rf_option_list l group by l.strategy_id, l.hist_stage) l
                                        on l.strategy_id = p.strategy_id
                                        and l.hist_stage=p.hist_stage
                       ) p
                               on inv.pool_id = p.pool_id
                                
                              
                  where 1=1 and d.status in (0,1,7,6,4,14)  
                            and d.program_type in ('isz')    
                            and r.currency='USD'
                            and r.rate_date> to_date('01/03/2017', 'dd/mm/yyyy') -- уменьшение объема выборки 
                  
              ) dog 
           --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------       
   )q 
  --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
          
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
--and q.pool_id=17
--and q.strategy_id=9 
--and q.DATE_OPTION = to_date('26/09/2019', 'dd/mm/yyyy') 
order by p.pool_id
;
