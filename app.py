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
select to_date(sysdate, 'dd/mm/yyyy') bI
from dual

"""

  def conjure_sql_query(pool_id,calc_date,sql_query = sql_query):
    valid_sql_query = sql_query.format(
      pool_id = pool_id,
      calc_date = calc_date
      )
    c.execute(sql_query)
     # обрабатываем SQL ответ
    header_list = []
    for i in c.description:
        header_list.append(i[0])
    header_list = tuple(header_list)
    rows = [row for row in c]

    ###### placeholder!!!
    header_list = []
    rows = [[],[]]
    #return {'header_list' : header_list, 'rows': rows}
  
  end_dict = conjure_sql_query(pool_id,calc_date)
  header_list = ["ИД Пула", "Остаток", "Дата","Комментарий"]
  rows = [['5','55545','segodnya','bI']]
  response_dict = {'header_list' : header_list, 'rows': rows}


  print(json.dumps(response_dict))
  return json.dumps(response_dict)


@app.route("/")
def root():
  return render_template('index.html')

if __name__ == '__main__':
  app.run(host="::", port=82, debug = True)