from flask import render_template, jsonify, request
from app import app
import pymysql as mdb
import datetime
from sklearn.externals import joblib
import pandas as pd
import numpy as np

db = mdb.connect(user="root", host="localhost", passwd='FsI786h4', db="ticketpricedb", charset='utf8')

@app.route('/')
@app.route('/index')
def index():
	event_ids = []
	with db:
		cur = db.cursor()
		cur.execute("SELECT game_name FROM event_char;")
		query_results = cur.fetchall()
		for result in query_results:
			event_ids.append(result[0])

	data = {
		"event_ids": event_ids
	}
	
	return render_template("index_js.html", data=data)

@app.route('/analytics')
def analytics():
	return render_template("analytics.html")


@app.route('/test')
def matrix_test():
	return render_template("matrix_test.html")



@app.route('/db')
def cities_page():
    with db: 
        cur = db.cursor()
        cur.execute("SELECT Name FROM city LIMIT 15;")
        query_results = cur.fetchall()
    cities = ""
    for result in query_results:
        cities += result[0]
        cities += "<br>"
    return cities

@app.route("/db_fancy")
def cities_page_fancy():
    with db:
        cur = db.cursor()
        cur.execute("SELECT Name, CountryCode, Population FROM City ORDER BY Population LIMIT 15;")

        query_results = cur.fetchall()
    cities = []
    for result in query_results:
        cities.append(dict(name=result[0], country=result[1], population=result[2]))
    return render_template('cities.html', cities=cities) 

@app.route("/db_json")
def cities_json():
    with db:
        cur = db.cursor()
        cur.execute("SELECT Name, CountryCode, Population FROM city ORDER BY Population DESC;")
        query_results = cur.fetchall()
    cities = []
    for result in query_results:
        cities.append(dict(name=result[0], country=result[1], population=result[2]))
    return jsonify(dict(cities=cities))


def price_opt(game_name_tag, section, seat, row):
	print "%s %s %s %s" % (game_name_tag, section, seat, row)
	events_data=[]
	db = mdb.connect(user="root", host="localhost", passwd='FsI786h4', db="ticketpricedb", charset='utf8')
	with db:
		cur = db.cursor()
		
		cur.execute('SELECT Hour, Minute, Year,Month,Day, event_id FROM event_char WHERE game_name = (%s);', game_name_tag)
		query_results = cur.fetchall()
		for result in query_results:
			events_data.append(result)
	
	events_data=events_data[0]
	
	event_hour=events_data[0]
	event_minute=events_data[1]
	event_year=events_data[2]
	event_month=events_data[3]
	event_day=events_data[4]
	
	
	event_id=events_data[5]
	
	if event_id==4403431 or event_id==4403433 or event_id==4403434:
		event_id=4403432

	
	event_datetime= datetime.datetime(event_year, event_month, event_day, event_hour, event_minute)
	t_minus = (event_datetime- datetime.datetime.now()).total_seconds()//60

	t_minus_days = int(t_minus//(24 *60))
	t_minus_hours = int((t_minus - t_minus_days*24*60)//60)
	t_minus_minutes= int(t_minus-  t_minus_days*24*60-  t_minus_hours*60)


	norm_factor=[]
	with db:
		cur = db.cursor()
		
		cur.execute('SELECT price_norm FROM norm_frame WHERE event_id= %s;', event_id)
		query_results = cur.fetchall()
		for result in query_results:
			norm_factor.append(result)
	
	norm_factor=norm_factor[0]
	norm_factor=norm_factor[0]
	

	
	seat_forrest= joblib.load('/Users/theblooms/Desktop/insight/seat_forrest.pkl') 
	probs = joblib.load('/Users/theblooms/Desktop/insight/prob_forrest.pkl') 
	
	deck= int(section/100)
	block=  section - deck*100
	
	in_data = np.array([deck ,block,row, seat, t_minus])

	expect_sale_price = float(seat_forrest.predict(in_data))
	
	price_test=[]
	pred=[]
	for i in range(275):
		b= float(i)/100
		price_pred= probs.predict_proba(b)
		price_pred=price_pred.tolist()
		price_pred=price_pred[0]
		price_pred=price_pred[1]
		pred.append(price_pred)
		price_test.append(b)

	out= {
		'x':price_test, 
		'pred':pred, 
		'expect_sale_price':expect_sale_price,
		'norm_factor': norm_factor,
		't_minus': t_minus,
		't_minus_days': t_minus_days, 
		't_minus_hours': t_minus_hours, 
		't_minus_minutes': t_minus_minutes
	}
	return out 

@app.route("/price_results", methods=['GET'])
def create_price():
	game_name_tag = str(request.args.get('event_id', 'Diamondbacks at Giants (September 9)'))
	section = int(request.args.get('section', 1))
	seat= int(request.args.get('seat', 1))
	row= int(request.args.get('row', 1))
	
	price_opt_result = price_opt(game_name_tag=game_name_tag, section=section, seat=seat,row=row)
	
	x=price_opt_result['x']
	pred=price_opt_result['pred']
	expect_sale_price = int(price_opt_result['expect_sale_price'])
	norm_factor = price_opt_result['norm_factor']
	t_minus = price_opt_result['t_minus']
	t_minus_days = price_opt_result['t_minus_days'] 
	t_minus_hours = price_opt_result['t_minus_hours']
	t_minus_minutes = price_opt_result['t_minus_minutes']
	
	
	x=pd.Series(x)
	pred=pd.Series(pred)
	
	expected_value = x* pred
	max_expv= float(1/(x[expected_value== expected_value.max()]))* expect_sale_price *norm_factor
	max_expv=int(max_expv)
	
	

	
	if t_minus < 0:
		text0= "This game has already occured"
	else:
		text0 = "It is  %s days, %s hours %s minutes until your game" %(t_minus_days, t_minus_hours, t_minus_minutes)
	
	
	text1 = "HelloIf you want to maximize your long run earnings you should sell it for  %s dollars" %max_expv
	text2 = "Most often, tickets like yours sell for %s dollars" %expect_sale_price
	#text3= "certain is %s" %percent_certain
	#text5= "%s out of 10 times, you can sell your ticket for %s dollars" %(percent_certain_out_ten,certain_price)
	#text2 = "The highest prices gaurenteed to sell 50 percent of the time is %s " %b

	data = {
	
		'text0': text0,
		'text1': text1,
		'text2': text2,
		'expected_sale_price': expect_sale_price ,
		'x':x,
		'pred':pred,
		'norm_factor':norm_factor,
		
		'game_name_tag':game_name_tag, 
		'section' :section,
		'seat':seat,
		'row': row,
	}
	return render_template('predicted_price.html', data=data)


@app.route("/price_results_json", methods=['GET'])
def price_results_json():
	print request.args.get('event_id')
	game_name_tag = str(request.args.get('event_id', 'Diamondbacks at Giants (September 9)'))
	section = int(request.args.get('section', 1))
	seat= int(request.args.get('seat', 1))
	row= int(request.args.get('row', 1))
	
	price_opt_result = price_opt(game_name_tag=game_name_tag, section=section, seat=seat,row=row)
	
	x=price_opt_result['x']
	pred=price_opt_result['pred']
	expect_sale_price = int(price_opt_result['expect_sale_price'])
	norm_factor = price_opt_result['norm_factor']
	t_minus = price_opt_result['t_minus']
	t_minus_days = price_opt_result['t_minus_days'] 
	t_minus_hours = price_opt_result['t_minus_hours']
	t_minus_minutes = price_opt_result['t_minus_minutes']
	
	
	x=pd.Series(x)
	pred=pd.Series(pred)
	
	expected_value = x* pred
	max_expv= float(1/(x[expected_value== expected_value.max()]))* expect_sale_price *norm_factor
	max_expv=int(max_expv)
	
	

	if t_minus < 0:
		text0= "This game has already occured"
	else:
		text0 = "It is  %s days, %s hours %s minutes until your game" %(t_minus_days, t_minus_hours, t_minus_minutes)
	
	
	text1 = "If you want to maximize your long run earnings you should sell it for $ %s" %max_expv
	text2 = "Most often, tickets like yours sell for $ %s" %expect_sale_price
	#text3= "certain is %s" %percent_certain
	#text5= "%s out of 10 times, you can sell your ticket for %s dollars" %(percent_certain_out_ten,certain_price)
	#text2 = "The highest prices gaurenteed to sell 50 percent of the time is %s " %b

	data = {
	
		'text0': text0,
		'text1': text1,
		'text2': text2,
		'expected_sale_price': expect_sale_price ,
		#'x':x,
		#'pred':pred,
		'norm_factor':norm_factor,
		'game_name_tag':game_name_tag, 
		'section' :section,
		'seat':seat,
		'row': row
	}
	return jsonify(data)

@app.route("/certain_price_json", methods=['GET'])
def certain_price_json():
	game_name_tag = str(request.args.get('event_id', 'Diamondbacks at Giants (September 9)'))
	section = int(request.args.get('section', 1))
	seat= int(request.args.get('seat', 1))
	row= int(request.args.get('row', 1))
	
	price_opt_result = price_opt(game_name_tag=game_name_tag, section=section, seat=seat,row=row)
	x=price_opt_result['x']
	pred=price_opt_result['pred']
	expect_sale_price = price_opt_result['expect_sale_price']
	norm_factor = price_opt_result['norm_factor']
	t_minus = price_opt_result['t_minus']
	t_minus_days = price_opt_result['t_minus_days'] 
	t_minus_hours = price_opt_result['t_minus_hours']
	t_minus_minutes = price_opt_result['t_minus_minutes']
	
	x= [ round(elem, 2) for elem in x]
	pred= [ round(elem, 2) for elem in pred]
	
	x=pd.Series(x)
	pred= pd.Series(pred)
	
	percent_certain = float(request.args.get('percent_certain',50))
	percent_certain = percent_certain/100
	certain_price=x[pred.index[pred > percent_certain]]
	certain_price=certain_price.min()
	percent_certain_out_ten = percent_certain*10

	# Calculation
	calculated_result =int((1/certain_price)* expect_sale_price *norm_factor)
	
	return jsonify(dict(result=calculated_result))













@app.route("/predicted_price_json")
def create_price_json():
    ####### MY CODE GOES HERE
    
    return jsonify(dict(prices=python_out))



@app.route("/jquery")
def index_jquery():
    return render_template('index_js.html') 


