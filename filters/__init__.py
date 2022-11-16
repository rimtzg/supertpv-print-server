from flask import request, url_for
import pytz
import humanize

from datetime import datetime
from bson.objectid import ObjectId

def humanize_date(date_to_parse):
    utc = pytz.utc
    timezone = pytz.timezone('America/Mexico_City')
    humanize.i18n.activate("es")

    if not(date_to_parse):
        date_to_parse = datetime.utcnow()

    date_to_parse = date_to_parse.replace(tzinfo=utc).astimezone(timezone).replace(tzinfo=None)

    return humanize.naturaltime(date_to_parse)

# @app.template_filter('date')
def date_filter(date_to_parse):
    utc = pytz.utc
    timezone = pytz.timezone('America/Mexico_City')

    if not(date_to_parse):
        date_to_parse = datetime.utcnow()

    if(type(date_to_parse) is str):
        date_to_parse = datetime.fromisoformat(date_to_parse)

    return date_to_parse.replace(tzinfo=utc).astimezone(timezone).strftime('%Y-%m-%d')

# @app.template_filter('calendar')
def calendar_filter(date_to_parse):
    if not(date_to_parse):
        date_to_parse = datetime.utcnow()

    return date_to_parse.strftime('%Y-%m-%d')

# @app.template_filter('time')
def time_filter(date_to_parse):
    utc = pytz.utc
    timezone = pytz.timezone('America/Mexico_City')

    if not(date_to_parse):
        date_to_parse = datetime.utcnow()

    if(type(date_to_parse) is str):
        date_to_parse = datetime.fromisoformat(date_to_parse)

    return date_to_parse.replace(tzinfo=utc).astimezone(timezone).strftime('%H:%M')

def datetime_filter(date_to_parse):
    utc = pytz.utc
    timezone = pytz.timezone('America/Mexico_City')

    if not(date_to_parse):
        date_to_parse = datetime.utcnow()

    if(type(date_to_parse) is str):
        date_to_parse = datetime.fromisoformat(date_to_parse)

    return date_to_parse.replace(tzinfo=utc).astimezone(timezone).strftime('%Y-%m-%d %H:%M')

def human_datetime_filter(date_to_parse):
    utc = pytz.utc
    timezone = pytz.timezone('America/Mexico_City')

    if not(date_to_parse):
        date_to_parse = datetime.utcnow()

    if(type(date_to_parse) is str):
        date_to_parse = datetime.fromisoformat(date_to_parse)

    return date_to_parse.replace(tzinfo=utc).astimezone(timezone).strftime("%d %b %Y %H:%M")

# @app.template_filter('numeric')
def integer_filter(int_to_parse):
    if not (int_to_parse):
        int_to_parse = 0

    return "{:,.0f}".format( int_to_parse )

def numeric_filter(float_to_parse):
    if not (float_to_parse):
        float_to_parse = 0

    return "{:,.2f}".format( float_to_parse )

# @app.template_filter('currency')
def currency_filter(float_to_parse):
    if not (float_to_parse):
        float_to_parse = 0

    return "$ {:,.2f}".format( float_to_parse )

# @app.template_filter('percent')
def percent_filter(float_to_parse):
    if not (float_to_parse):
        float_to_parse = 0
        
    return "{:,.0f} %".format( float_to_parse )

# @app.template_filter('type')
def type_of_filter(variable):
    return type(variable)

# @app.template_filter('oid')
def to_object_id_filter(variable):
    if not variable:
        variable = None
    return ObjectId(variable)

# @app.template_filter('str')
def str_filter(object):
    return object.__str__()

# @app.template_filter('url_pagination')
def url_pagination(page=None, search=None, items=None):
    if(request.args.get('page') and page == None):
        page = request.args['page']

    if(request.args.get('search') and search == None):
        search = request.args['search']

    if(request.args.get('items') and items == None):
        items = request.args['items']

    url = url_for(request.endpoint, **dict(request.view_args, **dict(request.args, **dict(page = page, search=search, items=items))) )
    return url

