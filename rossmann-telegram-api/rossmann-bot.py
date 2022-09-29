import os
import json
import requests
import pandas as pd

from flask import Flask, request, Response

# Constants
TOKEN = '5773939921:AAGWmJjjRYy7m-xl2_Ek7RZXee_8p4eywy8'

# Info about the bot
#https://api.telegram.org/bot5773939921:AAGWmJjjRYy7m-xl2_Ek7RZXee_8p4eywy8/getMe

# get updates
#https://api.telegram.org/bot5773939921:AAGWmJjjRYy7m-xl2_Ek7RZXee_8p4eywy8/getUpdates

# webhook 
#https://api.telegram.org/bot5773939921:AAGWmJjjRYy7m-xl2_Ek7RZXee_8p4eywy8/setWebhook?url=https://56176710bcd23c.lhrtunnel.link

# webhook Heroku
#https://api.telegram.org/bot5773939921:AAGWmJjjRYy7m-xl2_Ek7RZXee_8p4eywy8/setWebhook?url=https://tk-telegram-bot.herokuapp.com/

# send Message
#https://api.telegram.org/bot5773939921:AAGWmJjjRYy7m-xl2_Ek7RZXee_8p4eywy8/sendMessage?chat_id=1633695887&text=Oi Thomas, Eu estou bem, Obrigado!

def send_message(chat_id, text):
    url = 'https://api.telegram.org/bot{}/'.format(TOKEN)
    url = url + 'sendMessage?chat_id={}'.format(chat_id)

    r = requests.post(url, json={'text': text})
    print('Status Code {}'.format(r.status_code))

    return None

def load_dataset(store_id):
    # Loading test dataset
    df10 = pd.read_csv('test.csv')
    df_store_raw = pd.read_csv('store.csv')

    # Merge test dataset + store
    df_test = pd.merge(df10, df_store_raw, how='left', on='Store')

    # Choose store for prediction
    df_test = df_test[df_test['Store'] == store_id]

    if not df_test.empty:
        # Remove closed days
        df_test = df_test[df_test['Open'] != 0]
        df_test = df_test[~df_test['Open'].isnull()]
        df_test = df_test.drop('Id', axis=1)

        # Convert Dataframe to json
        data = json.dumps(df_test.to_dict(orient='records'))

    else:
        data = 'error'

    return data

def predict(data):
    # API Call
    url = 'https://prediction-sales-project.herokuapp.com/rossmann/predict'
    header = {'Content-type' : 'application/json'}
    data = data

    r = requests.post(url, data=data, headers=header)
    print('Status Code {}'. format(r.status_code))

    d1 = pd.DataFrame(r.json(), columns=r.json()[0].keys())

    return d1

def parse_message(message):
    chat_id = message['message']['chat']['id']
    store_id = message['message']['text']

    store_id = store_id.replace('/', '')

    try:
        store_id = int(store_id)

    except ValueError:
        store_id = 'error'

    return chat_id, store_id

# API Initialize
app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        message = request.get_json()

        chat_id, store_id = parse_message(message)

        if store_id != 'error':
            #loading data
            data = load_dataset(store_id)

            if data != 'error':

                #prediction
                d1 = predict(data)
                #calculation
                d2 = d1[['store', 'prediction']].groupby('store').sum().reset_index()
                #send message
                msg = 'A Loja Número {} venderá R${:,.2f} nas próximas 6 semanas.'.format(
                    d2['store'].values[0],
                    d2['prediction'].values[0])

                send_message(chat_id, msg)
                return Response('Ok', status=200)

            
            else:
                send_message(chat_id,'Loja não existente')
                return Response('Ok', status=200)

        else:
            send_message(chat_id, 'Por Favor, Insira um ID de Loja válido')
            return Response ('Ok', status=200)

    else:
        return '<h1> Rossmann Telegram BOT </h1>'

if __name__ == '__main__':
    port = os.environ.get('PORT', 5000)
    app.run(host='0.0.0.0', port=port)