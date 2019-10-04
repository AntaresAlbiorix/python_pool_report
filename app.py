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
  pool_id = request.args.get('pool_id')
  calc_date = request.args.get('calc_date')
  sql_query = """
	select 5*5 bI, sysdate werw
	from dual
	"""
  c.execute(sql_query)
  # обрабатываем SQL ответ
  header_list = [] #list of objects of any type
  for i in c.description:
      header_list.append(i[0])
  rows = [[],[]]   #may contain of lists as well (apparently)  
  header_list = tuple(header_list) #unchangeable list
  rows = [row for row in c] #list
  #header_list = ["ИД Пула", "Остаток", "Дата","Комментарий"]
  #rows = [['5','55545','segodnya','bI']]
  
  response_dict = {'header_list' : header_list, 'rows': rows}
  print (header_list)
  return json.dumps(response_dict) 

@app.route("/")
def root():
  return render_template('index.html')

if __name__ == '__main__':
  app.run(host="::", port=82, debug = True)