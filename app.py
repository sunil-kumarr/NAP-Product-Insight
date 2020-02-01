
import json
import pandas as pd
from flask import request
import io
import os
from flask import Flask, jsonify, abort, make_response, request


app = Flask(__name__)
path = 'netaporter_gb_similar.json'


product_json = []
df = pd.DataFrame()


with open(path) as fp:
    for product in fp.readlines():
        product_json.append(json.loads(product))
df = pd.json_normalize(product_json)
df['discounts'] = (df['price.regular_price.value']-df['price.offer_price.value'])/100.0


def apply_filters(temp_df,filter):
    if filter['operand1'] == 'discount':
        if filter["operator"] == '<':
            temp_df = df[df['discounts'] < filter["operand2"]]
        elif filter["operator"] == '>':
            temp_df = df[df['discounts'] > filter["operand2"]]
        else:
             temp_df = df[df['discounts'] == filter["operand2"]]
    elif filter["operand1"] == 'brand.name':
             temp_df = df[df['brand.name'] == filter["operand2"]]
    return temp_df

def get_query_type1(filters):
    ans = pd.DataFrame()
    for filter in filters:
        ans = apply_filters(ans,filter)
    return jsonify({'discounted_products_list': ans['_id.$oid'].to_list()})


def get_tasks_answer(request):
    if request.json['query_type'] == 'discounted_products_list':
         return get_query_type1(request.json['filters'])
    # elif request.query_type == 'discounted_products_count|avg_discount':
    #      return get_query_type2(request.filters)
    # elif request.query_type == 'expensive_list':
    #      return get_query_type3(request.filters)
    # elif request.query_type == 'competition_discount_diff_list':
    #      return get_query_type4(request.filters)
    return jsonify({'error':'invalid post request'})


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

@app.errorhandler(500)
def server_error(error):
    return make_response(jsonify({'error': 'Server failed'}), 500)


@app.route("/greendeck/discounts/", methods=['GET'])
def get_json_complete():
    return df.to_json(orient='columns')


@app.route('/greendeck/task1', methods=['POST'])
def get_tasks():
    return get_tasks_answer(request)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
