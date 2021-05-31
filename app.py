from flask import Flask
from flask import request
from flask import render_template
from collections import OrderedDict


import configparser
import os
import sys


SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(SCRIPT_DIR))

from utils import compile_sql,execute_sql

config = configparser.ConfigParser()
folder = os.path.abspath(os.path.dirname(__file__))
folder+='/'
config.read(folder + "snake.ini")
oracle_login = config['DEFAULT']['login']
oracle_password = config['DEFAULT']['password']

app = Flask(__name__, static_url_path='/static')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0


# функция для выгрузки инфы по переданным стратегиям и датам в виде таблицы
def get_pool_table(param_dict):
    valid_sql_query=compile_sql('nominal_per_pooolz.sql', param_dict)
    result_table = execute_sql(valid_sql_query)
    # обрабатываем SQL ответ
    s = '<table id="tab_result"><tr class="Heads">'
    for header in result_table['field_dict']:
        s = s + '<th>' + str(header) + '</th>'
    s = s + '</tr>'
    for row in result_table['rows']:
        s = s + '<tr>'
        for x in row:
            deficit_marker = ' style="color: #e91652;" ' if (str(x)[0] == '-') else ''
            s += '<td' + deficit_marker + '>' + str(x) + '</td>'
    s = s + '</tr>'
    s = s + '</table>'
    return s


# функция для выгрузки инфы по переданным стратегиям и датам в виде "карточки пула"
def get_pool_details(param_dict):
    valid_nominal_per_pooolz = compile_sql('nominal_per_pooolz.sql', param_dict)
    valid_opt_info_per_poolz = compile_sql('opt_info_per_poolz.sql', param_dict) # TODO: check the valuation_date < expiration_calc_date
    valid_eib_paid           = compile_sql('eib_paid.sql'          , param_dict)
    # выполняем все запросы сразу
    result_table=execute_sql(valid_nominal_per_pooolz, valid_opt_info_per_poolz, valid_eib_paid)
    # обрабатываем SQL ответ
    f     = result_table[0]['field_dict']
    rows  = result_table[0]['rows']
    f2    = result_table[1]['field_dict']
    rows2 = result_table[1]['rows']
    f3    = result_table[2]['field_dict']
    rows3 = result_table[2]['rows']
    # ========================================================
    # идем собирать карточку из списков
    s = ''
    nominal_table = OrderedDict((i[f['Номер пула']], i) for i in rows)  # i - строка из RS1
    eib_table = OrderedDict((i[f3['POOL_ID']], i) for i in rows3)
    asset_table = OrderedDict()
    for asset in rows2:
        pool_id = asset[f2['POOL_ID']]
        if pool_id in asset_table:
            asset_table[pool_id].append(asset)
        else:
            asset_table[pool_id] = [asset]

    for k, v in nominal_table.items():  # key, value
        # открываем карточку пула
        s = s + '<div class="optinfo">'
        # открываем блок с инфой по пулу
        s = s + '<div class="opt_column1"><h2>Карточка пула № ' + str(k) + '</h2><p/>'
        s = s + 'Стратегия: ' + str(v[f['Стратегия']]) + '<p/>'
        s = s + 'Дата инвестирования: ' + str(v[f['Дата опциона']]) + '<p/>'
        s = s + 'Средний КУ: ' + str(v[f['Средний КУ']]) + '%' + '<p/>'
        # s = s + 'Курс USD: '  + str(v[f['Курс USD']]) + '<p/>'
        s = s + 'Сумма брутто премий (руб.): ' + str(v[f['Брутто-премия (руб.)']]) + '<p/>'
        # s = s + 'Номинал по договорам: '  + str(v[f['Номинал по договорам']]) + '<p/>'
        # s = s + 'Остаток от текущ. пула: '  + str(v[f['Остаток от текущ. пула']]) + '<p/>'
        # s = s + 'Хвост от предыдущего пула: '  + str(v[f['Хвост']]) + '<p/>'
        # s = s + 'Итого остаток номинала: '  + str(v[f['Итого остаток']]) + '<p/>'
        # s = s + 'Лимит продаж: '  + str(v[f['Лимит продаж']]) + '<p/>'
        if k in eib_table and str(eib_table[k][f3['STATUS']]) == '5':
            s = s + 'Сумма возмещения (руб.): ' + str(eib_table[k][f3['SETTLE_RUR']]) + '<p/>'
            s = s + 'Сумма ДИД по нерасторгнутым (руб.): ' + str(eib_table[k][f3['EIB_NONLAPSE']]) + '<p/>'
            s = s + 'Сумма ДИД по заявленным убыткам (руб.): ' + str(eib_table[k][f3['BONUS_CLAIMED']]) + '<p/>'
            s = s + 'Курсовая разница: ' + str(eib_table[k][f3['K']]) + '<p/>'
        s = s + '</div>'
        # собираем блок с активами по пулу
        d = '<div class="opt_column2"><h2>Инфа по активам:  </h2><p/>'
        if k not in asset_table:
            d = d + 'Опционы по пулу не найдены' + '</div>'
        else:
            for asset in asset_table[k]:
                # открываем блок для одной бумаги
                d = d + '<div>'
                # d = d + 'Номер пула: '  + str(k) + '<p/>'
                d = d + '<h4>ISIN: ' + str(asset[f2['ISIN']]) + '</h4><p/>'
                # d = d + 'Дата инвестирования: '  + str(asset[f2['INVEST_START_DATE']]) + '<p/>'
                d = d + 'Дата покупки: ' + str(asset[f2['TRANSACTION_DATE']]) + '<p/>'
                d = d + 'Цена покупки: ' + str(asset[f2['OPTION_PRICE']]) + '<p/>'
                d = d + 'Купленный номинал (USD): ' + str(asset[f2['FV_USD']]) + '<p/>'
                d = d + 'Дата последней переоценки: ' + str(asset[f2['CALC_DATE']]) + '<p/>'
                d = d + 'Доходность опциона: ' + str(asset[f2['BS_VALUE']]) + '<p/>'
                d = d + 'Дата экспирации: ' + str(asset[f2['INVEST_END_DATE']]) + '<p/>'
                if str(asset[f2[
                    'STATUS']]) == '5':  # размер выплаты от эмитента выводим только по истекшим опционам (офк)
                    d = d + 'Сумма возмещения (USD): ' + str(asset[f2['SUM_CUR']]) + '<p/>'
                d = d + '</div>'
            d = d + '</div>'  # закрыли блок с активами
        s = s + d + '</div>'  # закрыли блок с карточкой пула
    return s


# ручка выгружает инфу по актуальному списку пулов (за последние 30 дней)
@app.route("/apriori")
def apriori():
    # переменные с веб-формы
    mode = request.args.get('mode')  # формат вывода информации
    status = request.args.get('status')  # выгрузка с лапсами или без
    valid_sql_query = compile_sql('default_pool_list.sql')
    result_table = execute_sql(valid_sql_query)
    # записываем результаты запроса в переменные
    strat_list = []
    optdate_list = []
    f = result_table['field_dict']
    for row in result_table['rows']:
        strat_list.append(str(row[f['STRATEGY_ID']]))
        optdate_list.append(row[f['DATE_OPT']])
    # присвоение значений переменным
    strat = ','.join(strat_list)
    optdate = "to_date('" + "', 'dd.mm.yyyy'), to_date('".join(optdate_list) + "', 'dd.mm.yyyy')"
    if status == '1':
        status = "0,1,7,4"
    else:
        status = "0,1,7,4,6"
    # сбор параметров для передачи в следующую ручку с основным запросом
    param_dict = {
        'strat': strat
        , 'optdate': optdate
        , 'status': status
    }
    if mode == 'table':
        return get_pool_table(param_dict)
    else:
        return get_pool_details(param_dict)


# ручка вытаскивает инфу по выбранным пулам
@app.route("/get_selected_pools")
def get_selected_pools():
    # переменные с веб-формы
    mode = request.args.get('mode')  # формат вывода информации
    status = request.args.get('status')  # выгрузка с лапсами или без
    # присвоение значений переменным
    strat = request.args.get('strat')
    optdate = request.args.get('optdate')
    if status == '1':
        status = "0,1,7,4"
    else:
        status = "0,1,7,4,6"
    # сбор параметров для передачи в следующую ручку с основным запросом
    param_dict = {
        'strat': strat
        , 'optdate': optdate
        , 'status': status
    }
    if mode == 'table':
        return get_pool_table(param_dict)
    else:
        return get_pool_details(param_dict)


# ручка вытаскивает актуальный список дат для выбранной стратегии
@app.route("/get_pool_list")
def get_pool_list():
    strat = request.args.get('strat')
    param_dict = {
        'strat': strat
    }
    valid_sql_query = compile_sql('pool_list.sql', param_dict)
    result_table=execute_sql(valid_sql_query)
    # обрабатываем SQL ответ
    # собираем список чекбоксов с датами
    s = '<h4  style="padding: 0px; margin:0px;margin-bottom:5px;">Даты инвестирования:</h4>'
    s = s + '<input type="button" name="Check_All_opts" value="Снять все" class="chkbtn"	onClick="master_check(\'optdate[]\')" id = "optdate[]"> </br>'
    for row in result_table['rows']:
        for x in row:
            s = s + '<input type="checkbox"  name="optdate[]"   value = "' + str(x) + '" checked > ' + str(x) + ' <Br/>'

    return s


@app.route("/")
def root():
    return render_template('index.html')


if __name__ == '__main__':
    #app.run(host='0.0.0.0', port=82, debug=True)
    app.run()
