from flask import Flask, jsonify, Response, request, after_this_request
import mysql.connector
import pandas as pd
import json
import joblib
from sklearn.tree import _tree
import numpy as np

app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'HELLO DANI'


mydb = mysql.connector.connect(
    host="freedb.tech",
    port=3306,
    user="freedbtech_etardata",
    passwd="etardata2021",
    database="freedbtech_etardatadb"
)

cursor = mydb.cursor()

query_indicator_electricidade = "SELECT indicator_table.indicator_name, indicator_table.indicator_type, indicator_table.units, indicator_value_table.sub_type, indicator_value_table.input, indicator_value_table.value, indicator_value_table.date, indicator_value_table.city_name FROM indicator_table INNER JOIN indicator_value_table ON indicator_table.id = indicator_value_table.indicator"
cursor.execute(query_indicator_electricidade)
result_indicator_electricidade = cursor.fetchall()

dados = pd.DataFrame((result_indicator_electricidade), columns=[
                     'indicator_name', 'indicator_type', 'units', 'sub_type', 'input', 'value', 'date', 'city_name'])


@app.route('/dados')
def dados():
    @after_this_request
    def add_header(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    #result = data.to_json(orient="records")
    return Response(data.to_json(orient="records"), mimetype='application/json')


@app.route('/prediction', methods=['GET', 'POST'])
def prediction():
    @after_this_request
    def add_header(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    if request.method == 'POST':
        print(request.form)
        #result_post = request.form
        pred = [[request.form['azoto_total_em_Afluente_Bruto'], request.form['cqo_em_Efluente_Tratado'],
                 request.form['sst_em_Afluente_Bruto'], request.form['amonia_em_Efluente_Tratado'],	request.form['ortofosfatos_em_Efluente_Tratado']]]
    loaded_model = joblib.load('dt_model.sav')
    prediction = loaded_model.predict(pred)
    result = {'azoto_total_em_Afluente_Bruto': request.form['azoto_total_em_Afluente_Bruto'], 'cqo_em_Efluente_Tratado': request.form['cqo_em_Efluente_Tratado'], 'sst_em_Afluente_Bruto': request.form['sst_em_Afluente_Bruto'],
              'amonia_em_Efluente_Tratado': request.form['amonia_em_Efluente_Tratado'], 'ortofosfatos_em_Efluente_Tratado': request.form['ortofosfatos_em_Efluente_Tratado'], 'previsao': str(prediction[0])}
    return result


def get_rules(tree, feature_names, class_names):
    tree_ = tree.tree_
    feature_name = [
        feature_names[i] if i != _tree.TREE_UNDEFINED else "undefined!"
        for i in tree_.feature
    ]

    paths = []
    path = []

    def recurse(node, path, paths):

        if tree_.feature[node] != _tree.TREE_UNDEFINED:
            name = feature_name[node]
            threshold = tree_.threshold[node]
            p1, p2 = list(path), list(path)
            p1 += [f"({name} <= {np.round(threshold, 3)})"]
            recurse(tree_.children_left[node], p1, paths)
            p2 += [f"({name} > {np.round(threshold, 3)})"]
            recurse(tree_.children_right[node], p2, paths)
        else:
            path += [(tree_.value[node], tree_.n_node_samples[node])]
            paths += [path]

    recurse(0, path, paths)

    # sort by samples count
    samples_count = [p[-1][1] for p in paths]
    ii = list(np.argsort(samples_count))
    paths = [paths[i] for i in reversed(ii)]

    rules = []
    for path in paths:
        rule = "Se "

        for p in path[:-1]:
            if rule != "Se ":
                rule += " e "
            rule += str(p)
        rule += " então "
        if class_names is None:
            rule += "o valor é: "+str(np.round(path[-1][0][0][0], 3))
        else:
            classes = path[-1][0][0]
            l = np.argmax(classes)
            rule += f"class: {class_names[l]} (proba: {np.round(100.0*classes[l]/np.sum(classes),2)}%)"
        #rule += f" | based on {path[-1][1]:,} samples"
        rules += [rule]

    return rules


@app.route('/rules')
def rules():
    rules_array = []

    @after_this_request
    def add_header(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    #result_post = request.form
    loaded_model = joblib.load('dt_model.sav')
    dataframe_for_columns_name = pd.DataFrame({'Azoto total em Afluente Bruto': 111, 'CQO em Efluente Tratado': 111,
                                              'SST em Afluente Bruto': 111, 'Amonia em Efluente Tratado': 111, 'Ostofosfatos em Efluente Tratado': 111}, index=[0])
    rules = get_rules(loaded_model, dataframe_for_columns_name.columns, None)
    for r in rules:
        rules_array.append(r)
    return jsonify(rules_array)


if __name__ == '__main__':
    app.run()
