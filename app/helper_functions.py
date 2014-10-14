
def price_opt(game_name_tag, section, seat, row, prob_threshold=.5):

	import pymysql as mdb
	import datetime
	from sklearn.externals import joblib
	import pandas as pd
	import numpy as np
	
	from helper_functions import price_opt

	#This prints the querry information, to confirm in python the correct game is being consesiderd
	print "%s %s %s %s" % (game_name_tag, section, seat, row)
	
	#This accesses the database to import the game level data
	events_data=[]
	db = mdb.connect(user="root", host="localhost", passwd='FsI786h4', db="ticketpricedb", charset='utf8')
	with db:
		cur = db.cursor()
		cur.execute('SELECT Hour, Minute, Year,Month,Day, event_id FROM event_char WHERE game_name = (%s);', game_name_tag)
		query_results = cur.fetchall()
		for result in query_results:
			events_data.append(result)


	
	events_data=events_data[0]
	
	#This parses the date infromation from the database to get game time data
	event_hour=events_data[0]
	event_minute=events_data[1]
	event_year=events_data[2]
	event_month=events_data[3]
	event_day=events_data[4]
	
	event_datetime= datetime.datetime(event_year, event_month, event_day, event_hour, event_minute)
	t_minus = (event_datetime- datetime.datetime.now()).total_seconds()//60

	t_minus_days = int(t_minus//(24 *60))
	t_minus_hours = int((t_minus - t_minus_days*24*60)//60)
	t_minus_minutes= int(t_minus-  t_minus_days*24*60-  t_minus_hours*60)

	#This ensure that past games are fitted assumung tickets are at game time price
	if t_minus <0:
		t_minus=0 

	event_id=events_data[5]

	#For the moment the the database only uses game 440342 to Normalize the data. This will be fixed for teh final verison
	##########FIX ME####################
	if event_id==4403431 or event_id==4403433 or event_id==4403434:
		event_id=4403432

	#This querries the normalization table from the database (created each time the database is updated with new data

	norm_factor=[]
	with db:
		cur = db.cursor()
		
		cur.execute('SELECT price_norm FROM norm_frame WHERE event_id= %s;', event_id)
		query_results = cur.fetchall()
		for result in query_results:
			norm_factor.append(result)

	norm_factor=norm_factor[0]
	norm_factor=norm_factor[0]
	
	#This loads the random forrests fit models in the database
	#Remember to make this relative before pulling online
	########FIX ME#################
	seat_forrest= joblib.load('.//RFpickle//seat_forrest.pkl') 
	probs = joblib.load('.//RFpickle//prob_forrest.pkl') 
	
	
	#This parses the Section Information (uploaded from a ticket, into a section and a deck)
	deck= int(section/100)
	block=  section - deck*100
	
	#This uses the "seat forrest" random forrest model to predict the 'normalized' selling price for a ticket
	in_data = np.array([deck ,block,row, seat, t_minus])

	expect_sale_price = float(seat_forrest.predict(in_data))
	
	
	#This is calclated the probabilit of selling a ticket
	#For a range (from .5 to 2.75) of list price to expected sale price ratios
	#This uses the probability estimates from the random forrests classification model
	price_ratios=[]
	predicted_probs=[]

	
	for i in range (250):
		b= float(i+50)/100
		predicted_prob= probs.predict_proba(b)
		predicted_prob=predicted_prob.tolist()
		predicted_prob=predicted_prob[0]
		predicted_prob=predicted_prob[0]
		predicted_probs.append(predicted_prob)
		price_ratios.append(b)



	#This rounds the predicted probability to nearest 1%
	#Equal to the granularity of the interface

	#This converts the outcomes to pandas series for
	price_ratios=pd.Series(price_ratios)
	predicted_probs= pd.Series(predicted_probs)
	
	data= pd.DataFrame({'price_ratios': price_ratios, 'predicted_probs':predicted_probs})
	data= data.drop_duplicates(['predicted_probs'])
	price_ratios= data['price_ratios']
	predicted_probs= data['predicted_probs']


	#To Calculate the maximum expected value price
	#The price ratio is multiple by the predicted probabilty, for each observation
	#This calculated the expected revuenue froma  sale
	#The one with the highest value, is the maximum expected value prices
	#The normalized price ratio is then multiplied the by expected sale price and the normalization factr
	#To put it back into "true" dollar to values
	#I also calculate the probability that the ticket sells, at that price

	expected_values=  price_ratios *predicted_probs
	max_expected_value = max(expected_values)
	max_expected_value_price_ratio= price_ratios[expected_values==max_expected_value]
	max_expected_value_price = int(max_expected_value_price_ratio * expect_sale_price * norm_factor)
	max_expected_value_prob= int(predicted_probs[expected_values==max_expected_value]*100)


	#To calculate the best ticket, with a certain likelihood of selling the ticket
	#We follow the same process, but sensor the data such that 
	#the prob is greater than the probabiliity threshold
	remaining_price_ratios= price_ratios[predicted_probs>=prob_threshold]
	max_remaining_price_ratio = max(remaining_price_ratios)
	max_remaining_expected_value_price = int(max_remaining_price_ratio * expect_sale_price * norm_factor)
	max_remaining_expected_value_prob= int(predicted_probs[price_ratios==max_remaining_price_ratio]*100)


	adjusted_sale_price= expect_sale_price* norm_factor

	#This section formats the results to be written out to the webite
	if t_minus == 0:
		text0= "This game has already occured, but you can explore anyway!"
	else:
		text0 = "It is  %s days, %s hours %s minutes until your game" %(t_minus_days, t_minus_hours, t_minus_minutes)
	text1 = "If you sell tickets frequently and want to maximize your expected earnings you should sell it for $%s" %str(max_expected_value_price)
	text1b = "There is a %s percent chance the ticket sells at this price" %str(max_expected_value_prob)
	text2 = "Using this price, you would earn an additional $%s compared to the typical seller" %str(int(max_expected_value_price-adjusted_sale_price))

	db.close()
	#This returns the resul in a list 
	out= {
		'text0':text0, 
		'text1':text1, 
		'text1b':text1b, 
		'text2':text2, 
		'predprice': max_remaining_expected_value_price}
	return out 
