from flask import Flask
from flask import request
from flask import render_template
import requests
import cx_Oracle
import json
import configparser


config = configparser.ConfigParser()
config.read('snake.ini')
oracle_login = config['DEFAULT']['login']
oracle_password = config['DEFAULT']['password']

app = Flask(__name__, static_url_path='/static')

#создаем соединение
dsn_tns = cx_Oracle.makedsn('172.20.0.202', '1521', service_name='mlife1')
conn = cx_Oracle.connect(user=oracle_login, password=oracle_password, dsn=dsn_tns, encoding = "UTF-8", nencoding = "UTF-8")
c = conn.cursor()

def get_pool_details(strat,optdate):
  fd = open('nominal_per_pooolz.sql', 'r')
  sql_query = fd.read()
  fd.close()
  valid_sql_query = sql_query.format(
    strat   = strat,
    optdate = optdate
    )
  print (valid_sql_query)
  #отправляем SQL запрос
  c.execute(valid_sql_query) 
  # обрабатываем SQL ответ
  s = '<table id="tab_result"><tr class="Heads">'  
  for header in c.description:
    s = s + '<th>'+ str(header[0]) + '</th>'
  s = s + '</tr>' 
  for row in c:  
    s = s + '<tr>'  
    for x in row:  
       s = s + '<td>' + str(x) + '</td>'  
  s = s + '</tr>' 
  s = s + '</table>' 
  print('start'+s+'end')
  return s 

@app.route("/apriori")
def apriori():
  fd = open('default_pool_list.sql', 'r')
  sql_query = fd.read()
  fd.close()
  valid_sql_query = sql_query
  #отправляем SQL запрос
  c.execute(valid_sql_query) 
  #функция для привязки названий столбцов к их индексам 
  def fields(cursor):
    """ Given a DB API 2.0 cursor object that has been executed, returns
    a dictionary that maps each field name to a column index; 0 and up. """
    results = {}
    column = 0
    for d in cursor.description:
        results[d[0]] = column
        column = column + 1
    return results
  #обрабатываем SQL ответ
  f = fields(c)
  #записываем результаты запроса в переменные
  strat_list = []
  optdate_list=[]
  for row in c:
    strat_list.append(str(row[f['STRATEGY_ID']]))
    optdate_list.append(row[f['DATE_OPT']]) 
  strat=','.join(strat_list)
  optdate="to_date('"+"', 'dd.mm.yyyy'), to_date('".join(optdate_list)+"', 'dd.mm.yyyy')"; 
  return get_pool_details(strat, optdate)
 
@app.route("/get_pool_list")
def get_pool_list():
  strat   = request.args.get('strat')
  fd = open('pool_list.sql', 'r')
  sql_query = fd.read()
  fd.close()
  valid_sql_query = sql_query.format(
    strat   = strat
    )
  #отправляем SQL запрос
  c.execute(valid_sql_query) 
  # обрабатываем SQL ответ
  s = '<h4  style="padding: 0px; margin:0px;margin-bottom:5px;">Даты инвестирования:</h4>'
  s = s+'<input type="button" name="Check_All_opts" value="Снять все" class="chkbtn"	onClick="master_check(\'optdate[]\')" id = "optdate[]"> </br>'  
  for row in c:  
    for x in row:  
       s = s + '<input type="checkbox"  name="optdate[]"   value = "' + str(x) + '" checked > ' + str(x) + ' <Br/>'
  return s 

@app.route("/get_selected_pools")
def get_selected_pools():
  print('ya tut')
  strat = request.args.get('strat')
  optdate = request.args.get('optdate')
  print(strat)
  print(optdate)
  return get_pool_details(strat, optdate)
 
  
@app.route("/")
def root():
  return render_template('index.html')

if __name__ == '__main__':
  app.run(host="::", port=82, debug = True)