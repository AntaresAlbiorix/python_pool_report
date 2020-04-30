from flask import Flask
from flask import request
from flask import render_template
from collections import OrderedDict
import cx_Oracle
import configparser



config = configparser.ConfigParser()
config.read('snake.ini')
oracle_login = config['DEFAULT']['login']
oracle_password = config['DEFAULT']['password']

app = Flask(__name__, static_url_path='/static')


# функция для привязки названий столбцов к их номерам
def fields(cursor):
  """ Given a DB API 2.0 cursor object that has been executed, returns
  a dictionary that maps each field name to a column index; 0 and up. """
  results = OrderedDict()
  column = 0
  for d in cursor.description:
    results[d[0]] = column
    column = column + 1
  return results


def execute_sql(sql_template, param_dict=None):
  with open(sql_template, 'r') as fd:
    sql_query = fd.read()
  if param_dict==None:
    valid_sql_query = sql_query
  else:
    valid_sql_query = sql_query.format(**param_dict)
 #создаем соединение
  dsn_tns = cx_Oracle.makedsn('172.20.2.36', '1521', service_name='mlife2')
  conn = cx_Oracle.connect(user=oracle_login, password=oracle_password, dsn=dsn_tns, encoding = "UTF-8", nencoding = "UTF-8")
  #отправляем SQL запрос
  c = conn.cursor()
  c.execute(valid_sql_query)
  # обрабатываем SQL ответ
  f = fields(c)
  rows = c.fetchall()
  c.close()
  conn.close()
  return {
    'field_dict' : f
  , 'rows': rows
  }


#функция для выгрузки инфы по переданным стратегиям и датам в виде таблицы
def get_pool_table(param_dict):
  result_table = execute_sql ('nominal_per_pooolz.sql',param_dict)
  # обрабатываем SQL ответ
  s = '<table id="tab_result"><tr class="Heads">'  
  for header in result_table['field_dict']:
    s = s + '<th>'+ str(header) + '</th>'
  s = s + '</tr>' 
  for row in result_table['rows']:
    s = s + '<tr>'  
    for x in row:  
       s = s + '<td>' + str(x) + '</td>'  
  s = s + '</tr>' 
  s = s + '</table>' 
  #print('start'+s+'end')
  return s 

#функция для выгрузки инфы по переданным стратегиям и датам в виде "карточки пула"
def get_pool_details(param_dict):
  result_table = execute_sql('nominal_per_pooolz.sql', param_dict)
  #записываем Recordset в списки
  header_list = result_table['field_dict']
  rows = result_table['rows']
  #запрос для получения инфы по активам по каждому пулу
  result_table = execute_sql('opt_info_per_poolz.sql', param_dict)
  #записываем Recordset в списки
  header_list2 = result_table['field_dict']
  rows2 = result_table['rows']
#========================================================  
  #идем собирать карточку из списков
  s = ''
  k0=0
  f=header_list
  m=header_list2
  for i in range(len(rows)):
    #открываем карточку пула
    s = s + '<div class="optinfo">'
    #открываем блок с инфой по пулу
    s = s + '<div class="opt_column1"><h2>Карточка пула № ' + str(rows[i][f['Номер пула']]) + '</h2><p/>'
    s = s + 'Стратегия: '  + str(rows[i][f['Стратегия']]) + '<p/>'
    s = s + 'Дата инвестирования: '  + str(rows[i][f['Дата инвестирования']]) + '<p/>'
    s = s + 'Средний КУ: ' + str(rows[i][f['Средний КУ']]) + '<p/>'
    s = s + 'Курс USD: '  + str(rows[i][f['Курс USD']]) + '<p/>'
    s = s + 'Брутто премия по договорам: '  + str(rows[i][f['Премия по договорам']]) + '<p/>'
    s = s + 'Номинал по договорам: '  + str(rows[i][f['Номинал по договорам']]) + '<p/>'
    s = s + 'Остаток от текущ. пула: '  + str(rows[i][f['Остаток от текущ. пула']]) + '<p/>'
    s = s + 'Хвост от предыдущего пула: '  + str(rows[i][f['Хвост']]) + '<p/>'
    s = s + 'Итого остаток номинала: '  + str(rows[i][f['Итого остаток']]) + '<p/>'
    s = s + 'Лимит продаж: '  + str(rows[i][f['Лимит продаж']]) + '<p/>'
    s = s + '</div>'      
    #собираем блок с активами по пулу
    d = '<div class="opt_column2"><h2>Инфа по активам:  </h2><p/>'
    for k in range(k0,len(rows2)):
        if str(rows[i][f['Номер пула']])!=str(rows2[k][m['POOL_ID']]):
            d=d+'Опционы по пулу не найдены'+'</div>'
            break
        #открываем блок для одной бумаги
        #print('normik')
        d=d+'<div>'
        d = d + 'Номер пула: '  + str(rows2[k][m['POOL_ID']]) + '<p/>'
        d = d + '<h4>ISIN: '  + str(rows2[k][m['ISIN']]) + '</h4><p/>'
        d = d + 'Дата покупки: '  + str(rows2[k][m['TRANSACTION_DATE']]) + '<p/>'
        d = d + 'Цена опциона: '  + str(rows2[k][m['OPTION_PRICE']]) + '<p/>'
        #для купонников пропускаем вывод переоценки
        if str(rows2[k][m['COUPON']]) == '0':
            d = d + 'Дата последней переоценки: ' + str(rows2[k][m['CALC_DATE']]) + '<p/>'
            d = d + 'Оценка опциона: '  + str(rows2[k][m['BS_VALUE']]) + '<p/>'
        d = d + 'Купленный номинал: '  + str(rows2[k][m['FV_USD']]) + '<p/>'
        d = d + 'Дата инвестирования: '  + str(rows2[k][m['INVEST_START_DATE']]) + '<p/>'
        d = d + 'Дата экспирации: '  + str(rows2[k][m['INVEST_END_DATE']]) + '<p/>'
        d=d+'</div>'
        if k+1==len(rows2): 
            d = d + '</div>'
        elif str(rows2[k][m['POOL_ID']]) != str(rows2[k+1][m['POOL_ID']]):    
            d = d + '</div>'
            k0=k+1
            break     			
    s = s + d+ '</div>'
  return s


#ручка выгружает инфу по актуальному списку пулов 
@app.route("/apriori")
def apriori():
  print('ya apriori')
  mode = request.args.get('mode')
  print (mode)
  result_table = execute_sql('default_pool_list.sql')
  #записываем результаты запроса в переменные
  strat_list = []
  optdate_list=[]
  f=result_table['field_dict']
  for row in result_table['rows']:
    strat_list.append(str(row[f['STRATEGY_ID']]))
    optdate_list.append(row[f['DATE_OPT']])
  strat = ','.join(strat_list)
  optdate = "to_date('" + "', 'dd.mm.yyyy'), to_date('".join(optdate_list) + "', 'dd.mm.yyyy')"
  param_dict={
    'strat':strat
    ,'optdate':optdate
  }
  if mode=='table':
    return get_pool_table(param_dict)
  else:	
    return get_pool_details(param_dict)
 
#ручка вытаскивает инфу по выбранным пулам
@app.route("/get_selected_pools")
def get_selected_pools():
  print('ya tut')
  strat = request.args.get('strat')
  optdate = request.args.get('optdate')
  param_dict={
    'strat' : strat
    ,'optdate':optdate
  }
  mode = request.args.get('mode')
  print (mode)
  if mode=='table':
    return get_pool_table(param_dict)
  else:	
    return get_pool_details(param_dict)
 


 #ручка вытаскивает актуальный список дат для выбранной стратегии
@app.route("/get_pool_list")
def get_pool_list():
  strat   = request.args.get('strat')
  param_dict = {
    'strat': strat
  }
  result_table = execute_sql('pool_list.sql', param_dict)

  #обрабатываем SQL ответ		
  #собираем список чекбоксов с датами
  s = '<h4  style="padding: 0px; margin:0px;margin-bottom:5px;">Даты инвестирования:</h4>'
  s = s+'<input type="button" name="Check_All_opts" value="Снять все" class="chkbtn"	onClick="master_check(\'optdate[]\')" id = "optdate[]"> </br>'  
  for row in result_table['rows']:
    for x in row:  
       s = s + '<input type="checkbox"  name="optdate[]"   value = "' + str(x) + '" checked > ' + str(x) + ' <Br/>'

  return s  


@app.route("/")
def root():
  return render_template('index.html')

if __name__ == '__main__':

  app.run(host='0.0.0.0', port=82, debug = True)
