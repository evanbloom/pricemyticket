from flask import render_template, jsonify, request
from app import app
import pymysql as mdb
import datetime
from sklearn.externals import joblib
import pandas as pd
import numpy as np
from helper_functions import price_opt

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


@app.route('/matrix2')
def matrix_test2():
	return render_template("matrix_test_177.html")

@app.route('/matrix3')
def matrix_test3():
	return render_template("matrix_test_315.html")


@app.route('/force')
def forcet():
	return render_template("force.html")


@app.route('/heatmap')
def heat():
	return render_template("heatmap.html")

@app.route('/slides')
def sides():
	return render_template("slides.html")



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




@app.route("/price_results_json", methods=['GET'])
def price_results_json():
	print "this is price results"
	print request.args.get('event_id')
	game_name_tag = str(request.args.get('event_id', 'Diamondbacks at Giants (September 9)'))
	section = int(request.args.get('section', 1))
	seat= int(request.args.get('seat', 1))
	row= int(request.args.get('row', 1))
	
	data = price_opt(game_name_tag=game_name_tag, section=section, seat=seat,row=row,  prob_threshold=.5)
	
	print jsonify(data)
	return jsonify(data)

@app.route("/certain_price_json", methods=['GET'])
def certain_price_json():
	print "this is certain results"
	print request.args.get('event_id')
	game_name_tag = str(request.args.get('event_id', 'Diamondbacks at Giants (September 9)'))
	section = int(request.args.get('section', 1))
	seat= int(request.args.get('seat', 1))
	row= int(request.args.get('row', 1))
	percent_certain = float(request.args.get('percent_certain',50))
	
	data = price_opt(game_name_tag=game_name_tag, section=section, seat=seat,row=row,  prob_threshold=percent_certain/100)
	calculated_result= data['predprice']


	return jsonify(dict(result=calculated_result))





@app.route("/predicted_price_json")
def create_price_json():
    ####### MY CODE GOES HERE
    
    return jsonify(dict(prices=python_out))



@app.route("/jquery")
def index_jquery():
    return render_template('index_js.html') 


