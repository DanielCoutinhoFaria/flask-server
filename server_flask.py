from flask import Flask, jsonify, Response, request, after_this_request
import mysql.connector
import pandas as pd
import json
import joblib

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

dados = pd.DataFrame((result_indicator_electricidade),columns=['indicator_name','indicator_type','units','sub_type','input','value','date','city_name'])

@app.route('/dados')
def dados():
    @after_this_request
    def add_header(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    #result = data.to_json(orient="records")
    return Response(data.to_json(orient="records"), mimetype='application/json')

@app.route('/prediction', methods=['GET','POST'])
def prediction():
    @after_this_request
    def add_header(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    if request.method == 'POST':
        print(request.form)
        #result_post = request.form
        pred = [[request.form['azoto_total_em_Afluente_Bruto'], request.form['cqo_em_Efluente_Tratado'], request.form['sst_em_Afluente_Bruto'], request.form['amonia_em_Efluente_Tratado'],	request.form['ortofosfatos_em_Efluente_Tratado']]]
    loaded_model = joblib.load('dt_model.sav')
    prediction = loaded_model.predict(pred)
    result = {'azoto_total_em_Afluente_Bruto':request.form['azoto_total_em_Afluente_Bruto'], 'cqo_em_Efluente_Tratado': request.form['cqo_em_Efluente_Tratado'], 'sst_em_Afluente_Bruto':request.form['sst_em_Afluente_Bruto'], 'amonia_em_Efluente_Tratado': request.form['amonia_em_Efluente_Tratado'], 'ortofosfatos_em_Efluente_Tratado': request.form['ortofosfatos_em_Efluente_Tratado'], 'previsao': str(prediction[0])}
    return result

if __name__ == '__main__':
    app.run()   