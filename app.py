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

app = Flask(__name__)

#создаем соединение
dsn_tns = cx_Oracle.makedsn('172.20.0.202', '1521', service_name='mlife1')
conn = cx_Oracle.connect(user=oracle_login, password=oracle_password, dsn=dsn_tns)
c = conn.cursor()

@app.route("/get_pool_details")
def get_pool_details():
  pool_id   = request.args.get('pool_id')
  calc_date = request.args.get('calc_date')
  sql_query = """
	select {pool_id}   *2 	bI
		,  {calc_date} *5 	werw
	from dual
	"""
  valid_sql_query = sql_query.format(
    pool_id   = pool_id,
    calc_date = calc_date
    )
  print (valid_sql_query)
  #отправляем SQL запрос
  c.execute(valid_sql_query) 
  # обрабатываем SQL ответ
  header_list = [] #list of objects of any type
  for i in c.description:
	  header_list.append(i[0])
  rows = [[],[]]   #may contain of lists as well (apparently)  
  header_list = tuple(header_list) #unchangeable list
  rows = [row for row in c] #list  
 
  response_dict = {'header_list' : header_list, 'rows': rows}
  
  return json.dumps(response_dict) 
  
@app.route("/")
def root():
  return render_template('index.html')

if __name__ == '__main__':
  app.run(host="::", port=82, debug = True)