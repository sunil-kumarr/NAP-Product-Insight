
import json
import pandas as pd
import io
import os
import gdown
from functools import partial
from flask_cors import CORS
from flask import Flask, jsonify, abort, request, make_response


app = Flask(__name__)

# load the json file into a list
product_json = []
path = 'netaporter_gb_similar.json'
with open(path) as fp:
    for product in fp.readlines():
        product_json.append(json.loads(product))

# normalize the deeply nested json to flat structure dataframe from product_json list
nap_dataframe = pd.json_normalize(product_json)

# new "discounts" column is created from regular and offer price of NAP productss
nap_dataframe['discounts'] = ((nap_dataframe['price.regular_price.value'] - nap_dataframe['price.offer_price.value'])/nap_dataframe['price.regular_price.value'])*100

# apply single filter from POST request on the dataframe here
def apply_filters(temp_nap_dataframe,filter):
    # TYPE 1 Filter: discount [<,>,==] val
    if filter['operand1'] == 'discount':
        if filter["operator"] == '<':
            temp_nap_dataframe = nap_dataframe[nap_dataframe['discounts'] < filter["operand2"]]
        elif filter["operator"] == '>':
            temp_nap_dataframe = nap_dataframe[nap_dataframe['discounts'] > filter["operand2"]]
        else:
             temp_nap_dataframe = nap_dataframe[nap_dataframe['discounts'] == filter["operand2"]]
    # TYPE 2 Filter: brand.name [==] 'gucci or ....'
    elif filter["operand1"] == 'brand.name':
             temp_nap_dataframe = nap_dataframe[nap_dataframe['brand.name'] == filter["operand2"]]
    return temp_nap_dataframe

# util function to apply different filters on dataframe using apply_filters function
def filter_dataframe(filters):
    temp_nap_dataframe = nap_dataframe
    for filter in filters:
        temp_nap_dataframe = apply_filters(temp_nap_dataframe,filter)
    return temp_nap_dataframe

# competitors website hash_id dict
WEBSITE_ID_HASH = {
 "farfetch_gb"       : "5d0cc7b68a66a100014acdb0" ,
 "mytheresa_gb"      : "5da94e940ffeca000172b12a" ,
 "matchesfashion_gb" : "5da94ef80ffeca000172b12c" ,
 "ssense_gb"         : "5da94f270ffeca000172b12e" ,
 "selfridges_gb"     : "5da94f4e6d97010001f81d72"
}

# helper function to get nap_product_list who's basket_price < nap_basket_price
def get_similar_items(comp_col_list,nap_frame):
    nap_product_ids = []
    #loop through each nap_dataframe row
    for index,row in nap_frame.iterrows():
         # basket_price for each row of NAP product
        basket_price_nap = row['price.basket_price.value']
         # loop through each competitor in websites column
        for comp_col in comp_col_list:
                 # loop for each similar product
                for sim_product in row[comp_col]:
                    # get the basket price for similiar product
                     basket_price_comp = sim_product['_source']['price']['basket_price']['value']
                     if basket_price_comp < basket_price_nap:
                         nap_product_ids.append(row['_id.$oid'])
                         break
    return nap_product_ids

# helper fucntion to get product_id having discount > n% from competitor X
# (Assuming competition filter is singular in filters i.e. comparision is only with one competition website)
def get_discount_diff(com_col,nap_frame,discount_diff):
    nap_product_ids = []
    # loop over each row of dataframe
    for index,row in nap_frame.iterrows():
        # get NAP product discount for current row
        discount_nap = row['discounts']
        # loop over similiar products list sold by competitor X : comp_col
        for product in row[com_col]:
            # get regular price of product sold by competitor X
            reg_price = product['_source']['price']['regular_price']['value']
            # get offer price of product sold by competitor X
            off_price = product['_source']['price']['offer_price']['value']
            # calculate discount %  of product sold by competitor X
            discount_comp = ((reg_price-off_price)/reg_price)*100.0
            # if discount differnce of NAP product and comp product is > n% add id to list
            if discount_nap - discount_comp > discount_diff:
                nap_product_ids.append(row['_id.$oid'])
    return nap_product_ids

# (QUESTION 1)
def get_query_type1(filters):
    # apply filters on dataframe
    ans = filter_dataframe(filters)
    # return the IDs based on filters
    return jsonify({'discounted_products_list': ans['_id.$oid'].to_list()})

# (QUESTION 2)
def get_query_type2(filters):
    # apply filters on dataframe
    ans = filter_dataframe(filters)
    #  return the discount count and avg discount
    return jsonify({'discounted_products_count': int(ans.discounts.count()) ,'avg_discount': round(float(ans.discounts.mean()),2)})

# (QUESTION 3)
def get_query_type3(filters):
    # apply filters on dataframe if any
    temp_dataframe = filter_dataframe(filters)
    expen_col = "similar_products.website_results."
    col = []
    # creating column names from website_hash_id
    for web_id in WEBSITE_ID_HASH.values():
        col.append(expen_col+web_id+".knn_items")
    # calling helper function to get nap_product_ids where they are selling at a price higher than any of the competition.
    nap_product_ids = get_similar_items(col,temp_dataframe)
    # return the IDs based on filters
    return jsonify({'epensive_list':nap_product_ids})

# (QUESTION 4)
def get_query_type4(filters):
    # apply filers on dataframe if any
    temp_dataframe = filter_dataframe(filters)
    expen_col = "similar_products.website_results."
    comp_col = ''
    discount_diff = 0
    # loop over specific filters
    for filter in filters:
        # (assuming only one filter of this type)
        if filter['operand1'] == 'competition':
            # creating column_name for competitor X
            comp_col = expen_col+filter['operand2']+".knn_items"
        # get the discount_diff asked in query
        if filter['operand1'] == 'discount_diff':
            discount_diff = filter['operand2']
    # calling the helper function to get the product_id having discount > n% from competitor X
    nap_product_ids = get_discount_diff(comp_col,temp_dataframe,discount_diff)
    # return Ids based on query
    return jsonify({"competition_discount_diff_list": nap_product_ids})

# function to identify different QUERY_TYPE
def get_tasks_answer(request):
    if not request.json :
        abort(400)
    # query type = 1
    if request.json['query_type'] == 'discounted_products_list':
         return get_query_type1(request.json['filters'])
    # query type = 2
    elif request.json['query_type'] == 'discounted_products_count|avg_discount':
         return get_query_type2(request.json['filters'])
    # query type = 3
    elif request.json["query_type"] == 'expensive_list':
         if not 'filters' in request.json:
            return get_query_type3([])
         else :
             return get_query_type3(request.json['filters'])
    # query type = 4
    elif request.json["query_type"] == 'competition_discount_diff_list':
         return get_query_type4(request.json["filters"])
    return jsonify({'error':'invalid post request'})

# respond to any page not found error
@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

# respond to any server side error
@app.errorhandler(500)
def server_error(error):
    return make_response(jsonify({'error': 'Server failed'}), 500)

# Test Function : to get columns in created dataframe
@app.route("/greendeck/columns/",methods=['GET'])
def get_columns():
    return jsonify({"columns":nap_dataframe.columns.to_list()})

# QUERY_TYPE = ANY : function to handle incoming POST request for all type query
@app.route('/greendeck/task', methods=['POST'])
def get_tasks():
    return get_tasks_answer(request)

# QUERY_TYPE = 1 : function to handle incoming POST request
@app.route('/greendeck/question1', methods=['POST'])
def get_task1():
    if not request.json :
        abort(400)
    return get_query_type1(request.json['filters'])

# QUERY_TYPE = 2 : function to handle incoming POST request
@app.route('/greendeck/question2', methods=['POST'])
def get_task2():
    if not request.json :
        abort(400)
    return get_query_type2(request.json['filters'])

# QUERY_TYPE = 3 : function to handle incoming POST request
@app.route('/greendeck/question3', methods=['POST'])
def get_task3():
    if not request.json :
        abort(400)
    if not 'filters' in request.json:
         return get_query_type3([])
    else :
         return get_query_type3(request.json['filters'])

# QUERY_TYPE = 4 : function to handle incoming POST request
@app.route('/greendeck/question4', methods=['POST'])
def get_task4():
    if not request.json :
        abort(400)
    return get_query_type4(request.json['filters'])

# start app
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
