
import json
import pandas as pd
from functools import partial
from flask_cors import CORS
from flask import request
import gdown
import io
import os
from flask import Flask, jsonify, abort, make_response, request

url = 'https://drive.google.com/a/greendeck.co/uc?id=19r_vn0vuvHpE-rJpFHvXHlMvxa8UOeom&export=download'


app = Flask(__name__)
CORS(app)
path = 'netaporter_gb_similar.json'


def init_files(dump_path):
    if dump_path.split('/')[0] not in os.listdir():
        os.mkdir(dump_path.split('/')[0])
    if os.path.exists(dump_path):
        pass
    else:
        gdown.download(url=url, output=dump_path, quiet=False)


product_json = []
df = None
#  load file in memory


# def prepare_dataset(path):
#     global df
with open(path) as fp:
    for product in fp.readlines():
        product_json.append(json.loads(product))
df = pd.json_normalize(product_json)


def get_discounts(discount_val):
    df['discounts'] = (df['price.regular_price.value']-df['price.offer_price.value'])/100.0
    ans = df[df['discounts'] > discount_val]
    return df['_id.$oid'].to_list()


@app.route("/greendeck/total/", methods=['GET'])
def get_json_complete():
    return df.to_json(orient='columns')


@app.route('/greendeck/task1', methods=['GET'])
def get_tasks():
    return jsonify({"discounted_products_list": get_discounts(df)})


if __name__ == '__main__':
    init_files('dumps/netaporter_gb.json')
    # prepare_dataset(path)
    app.run(debug=True, host='0.0.0.0', port=5000)
