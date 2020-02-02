
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
# data = pd.read_json("netaporter_gb_similar.json",lines=True,orient='columns')
df['discounts'] = ((df['price.regular_price.value'] - df['price.offer_price.value'])/df['price.regular_price.value'])*100


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


def filter_dataframe(filters):
    temp_df = df
    for filter in filters:
        temp_df = apply_filters(temp_df,filter)
    return temp_df


def get_query_type1(filters):
    ans = filter_dataframe(filters)
    return jsonify({'discounted_products_list': ans['_id.$oid'].to_list()})


def get_query_type2(filters):
    ans = filter_dataframe(filters)
    return jsonify({'discounted_products_count': int(ans.discounts.count()) ,'avg_discount': round(float(ans.discounts.mean()),2)})


WEBSITE_ID_HASH = {
#  "netaporter_gb"     : "5da6d40110309200045874e6" ,
 "farfetch_gb"       : "5d0cc7b68a66a100014acdb0" ,
 "mytheresa_gb"      : "5da94e940ffeca000172b12a" ,
 "matchesfashion_gb" : "5da94ef80ffeca000172b12c" ,
 "ssense_gb"         : "5da94f270ffeca000172b12e" ,
 "selfridges_gb"     : "5da94f4e6d97010001f81d72" 
}


def get_similar_items(web_col,nap_frame):
    ids = []
    for index,row in nap_frame.iterrows():
        basket_nap = row['price.basket_price.value']
        for col in web_col:
            if len(row[col]) > 0:
                for enemy in row[col]:
                     basket_enemy = enemy['_source']['price']['basket_price']['value']
                     if basket_enemy < basket_nap:
                         ids.append(row['_id.$oid'])
                         break 
    return jsonify({'epensive_list':ids})        
   

def get_query_type3(filters):

    temp_dataframe = filter_dataframe(filters)
    expen_col = "similar_products.website_results."
    col = []
    for web_id in WEBSITE_ID_HASH.values():
        col.append(expen_col+web_id+".knn_items")
    return get_similar_items(col,temp_dataframe)


def get_tasks_answer(request):
    if not request.json : 
        abort(400)
    if request.json['query_type'] == 'discounted_products_list':
         return get_query_type1(request.json['filters'])
    elif request.json['query_type'] == 'discounted_products_count|avg_discount':
         return get_query_type2(request.json['filters'])
    elif request.json["query_type"] == 'expensive_list':
         if not 'filters' in request.json:
            return get_query_type3([])
         else :
             return get_query_type3(request.json['filters'])
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
    return df['discounts'].to_json(orient='columns')

@app.route("/greendeck/columns/",methods=['GET'])
def get_columns():
    return jsonify({"columns":df.columns.to_list()})

@app.route('/greendeck/task', methods=['POST'])
def get_tasks():
    return get_tasks_answer(request)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)




'''
{
    "columns": [
        "name",
        "sku",
        "url",
        "description_text",
        "spider",
        "lv_url",
        "price_changes",
        "price_positioning",
        "price_positioning_text",
        "_id.$oid",
        "brand.name",
        "brand.sub_brand",
        "media.standard",
        "media.thumbnail",
        "meta.breadcrumbs.1",
        "meta.breadcrumbs.2",
        "meta.breadcrumbs.3",
        "meta.bert_original_classification.l1",
        "meta.bert_original_classification.l2",
        "meta.bert_original_classification.l3",
        "meta.bert_original_classification.l4",
        "meta.reference",
        "website_id.$oid",
        "price.offer_price.currency",
        "price.offer_price.value",
        "price.regular_price.currency",
        "price.regular_price.value",
        "price.basket_price.value",
        "price.basket_price.currency",
        "stock.available",
        "classification.l1",
        "classification.l2",
        "classification.l3",
        "classification.l4",
        "created_at.$date",
        "updated_at.$date",
        "similar_products.meta.total_results",
        "similar_products.meta.min_price.regular",
        "similar_products.meta.min_price.offer",
        "similar_products.meta.min_price.basket",
        "similar_products.meta.max_price.regular",
        "similar_products.meta.max_price.offer",
        "similar_products.meta.max_price.basket",
        "similar_products.meta.avg_price.regular",
        "similar_products.meta.avg_price.offer",
        "similar_products.meta.avg_price.basket",
        "similar_products.meta.avg_discount",
        "similar_products.website_results.5da94f4e6d97010001f81d72.meta.total_results",
        "similar_products.website_results.5da94f4e6d97010001f81d72.meta.min_price.regular",
        "similar_products.website_results.5da94f4e6d97010001f81d72.meta.min_price.offer",
        "similar_products.website_results.5da94f4e6d97010001f81d72.meta.min_price.basket",
        "similar_products.website_results.5da94f4e6d97010001f81d72.meta.max_price.regular",
        "similar_products.website_results.5da94f4e6d97010001f81d72.meta.max_price.offer",
        "similar_products.website_results.5da94f4e6d97010001f81d72.meta.max_price.basket",
        "similar_products.website_results.5da94f4e6d97010001f81d72.meta.avg_price.regular",
        "similar_products.website_results.5da94f4e6d97010001f81d72.meta.avg_price.offer",
        "similar_products.website_results.5da94f4e6d97010001f81d72.meta.avg_price.basket",
        "similar_products.website_results.5da94f4e6d97010001f81d72.meta.avg_discount",
        "similar_products.website_results.5da94f4e6d97010001f81d72.knn_items",
        "similar_products.website_results.5da94f270ffeca000172b12e.meta.total_results",
        "similar_products.website_results.5da94f270ffeca000172b12e.meta.min_price.regular",
        "similar_products.website_results.5da94f270ffeca000172b12e.meta.min_price.offer",
        "similar_products.website_results.5da94f270ffeca000172b12e.meta.min_price.basket",
        "similar_products.website_results.5da94f270ffeca000172b12e.meta.max_price.regular",
        "similar_products.website_results.5da94f270ffeca000172b12e.meta.max_price.offer",
        "similar_products.website_results.5da94f270ffeca000172b12e.meta.max_price.basket",
        "similar_products.website_results.5da94f270ffeca000172b12e.meta.avg_price.regular",
        "similar_products.website_results.5da94f270ffeca000172b12e.meta.avg_price.offer",
        "similar_products.website_results.5da94f270ffeca000172b12e.meta.avg_price.basket",
        "similar_products.website_results.5da94f270ffeca000172b12e.meta.avg_discount",
        "similar_products.website_results.5da94f270ffeca000172b12e.knn_items",
        "similar_products.website_results.5d0cc7b68a66a100014acdb0.meta.total_results",
        "similar_products.website_results.5d0cc7b68a66a100014acdb0.meta.min_price.regular",
        "similar_products.website_results.5d0cc7b68a66a100014acdb0.meta.min_price.offer",
        "similar_products.website_results.5d0cc7b68a66a100014acdb0.meta.min_price.basket",
        "similar_products.website_results.5d0cc7b68a66a100014acdb0.meta.max_price.regular",
        "similar_products.website_results.5d0cc7b68a66a100014acdb0.meta.max_price.offer",
        "similar_products.website_results.5d0cc7b68a66a100014acdb0.meta.max_price.basket",
        "similar_products.website_results.5d0cc7b68a66a100014acdb0.meta.avg_price.regular",
        "similar_products.website_results.5d0cc7b68a66a100014acdb0.meta.avg_price.offer",
        "similar_products.website_results.5d0cc7b68a66a100014acdb0.meta.avg_price.basket",
        "similar_products.website_results.5d0cc7b68a66a100014acdb0.meta.avg_discount",
        "similar_products.website_results.5d0cc7b68a66a100014acdb0.knn_items",
        "similar_products.website_results.5da94ef80ffeca000172b12c.meta.total_results",
        "similar_products.website_results.5da94ef80ffeca000172b12c.meta.min_price.regular",
        "similar_products.website_results.5da94ef80ffeca000172b12c.meta.min_price.offer",
        "similar_products.website_results.5da94ef80ffeca000172b12c.meta.min_price.basket",
        "similar_products.website_results.5da94ef80ffeca000172b12c.meta.max_price.regular",
        "similar_products.website_results.5da94ef80ffeca000172b12c.meta.max_price.offer",
        "similar_products.website_results.5da94ef80ffeca000172b12c.meta.max_price.basket",
        "similar_products.website_results.5da94ef80ffeca000172b12c.meta.avg_price.regular",
        "similar_products.website_results.5da94ef80ffeca000172b12c.meta.avg_price.offer",
        "similar_products.website_results.5da94ef80ffeca000172b12c.meta.avg_price.basket",
        "similar_products.website_results.5da94ef80ffeca000172b12c.meta.avg_discount",
        "similar_products.website_results.5da94ef80ffeca000172b12c.knn_items",
        "similar_products.website_results.5da94e940ffeca000172b12a.meta.total_results",
        "similar_products.website_results.5da94e940ffeca000172b12a.meta.min_price.regular",
        "similar_products.website_results.5da94e940ffeca000172b12a.meta.min_price.offer",
        "similar_products.website_results.5da94e940ffeca000172b12a.meta.min_price.basket",
        "similar_products.website_results.5da94e940ffeca000172b12a.meta.max_price.regular",
        "similar_products.website_results.5da94e940ffeca000172b12a.meta.max_price.offer",
        "similar_products.website_results.5da94e940ffeca000172b12a.meta.max_price.basket",
        "similar_products.website_results.5da94e940ffeca000172b12a.meta.avg_price.regular",
        "similar_products.website_results.5da94e940ffeca000172b12a.meta.avg_price.offer",
        "similar_products.website_results.5da94e940ffeca000172b12a.meta.avg_price.basket",
        "similar_products.website_results.5da94e940ffeca000172b12a.meta.avg_discount",
        "similar_products.website_results.5da94e940ffeca000172b12a.knn_items",
        "positioning.page",
        "positioning.rank",
        "sizes",
        "discounts"
    ]
}
'''
