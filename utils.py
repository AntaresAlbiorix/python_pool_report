from collections import OrderedDict
import cx_Oracle


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


# функция для сборки запроса
def compile_sql(sql_template, param_dict=None):
    with open(folder + sql_template, 'r') as fd:
        sql_query = fd.read()
    if param_dict == None:
        valid_sql_query = sql_query
    else:
        valid_sql_query = sql_query.format(**param_dict)
    return valid_sql_query


# функция для подстановки списка параметров в шаблон запроса, установка соединения, выполнение запроса
def execute_sql(*valid_sql_queries):
    # создаем соединение
    dsn_tns = cx_Oracle.makedsn('172.20.2.36', '1521', service_name='mlife2')
    conn = cx_Oracle.connect(user=oracle_login, password=oracle_password, dsn=dsn_tns, encoding="UTF-8",
                             nencoding="UTF-8")
    c = conn.cursor()
    # отправляем SQL запрос
    rs = []
    for query in valid_sql_queries:
        c.execute(query)
        # обрабатываем SQL ответ
        f = fields(c)
        rows = c.fetchall()
        rs.append(
            {
                'field_dict': f,
                'rows': rows
            }
        )
    c.close()
    conn.close()
    return rs[0] if len(rs)==1 else rs

