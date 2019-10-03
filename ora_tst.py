
import requests
import cx_Oracle
import json
import configparser
config = configparser.ConfigParser()
config.read('snake.ini')
oracle_login = config['DEFAULT']['login']
oracle_password = config['DEFAULT']['password']




#создаем соединение
dsn_tns = cx_Oracle.makedsn('172.20.0.202', '1521', service_name='mlife1')
conn = cx_Oracle.connect(user=oracle_login, password=oracle_password, dsn=dsn_tns)
c = conn.cursor()


sql_query = """
select to_date(sysdate, 'dd/mm/yyyy') CMOTRI_SYDA
from dual
"""

c.execute(sql_query)
     # обрабатываем SQL ответ
header_list = []
for i in c.description:
      header_list.append(i[0])
header_list = tuple(header_list)
rows = [row for row in c]

    
print(header_list)
print(rows)



