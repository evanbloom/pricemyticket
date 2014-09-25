
#This imports all the packages that will be used in this file
import os
import pandas as pd
import numpy as np
import datetime
import string
import sklearn
import string
from pandas.io import sql
import pymysql as mdb




#This is a function that takes in single download sheet and cleans it for process

def clean_data (game_data):
    
    #This takes the section variable in the form <LL###>
    #and breaks it into two sub-variables
    #The letters extract informaion about the level 
    #The digits extraction about the section
    sh = game_data.section.str.extract('(?P<letter>[A-Z]*)(?P<digit>\d*)')
    
    
    #Merge the extracted data back into the dataframe
    game_data= game_data.join(sh)
    
    
    #Some data did not have section info, This data is ingnored the analysis
    game_data= game_data[game_data.digit != ""]
    #This changes the section into an intiger
    game_data['digit'] = game_data['digit'].apply(int)
    game_data['price'] = game_data['price'].apply(float)
    
    
    #The section variable has two pieces of information
    #This first digit of the section vairable is deck (1,2,3)
    game_data['deck']= np.floor_divide(game_data['digit'],100)
    
    #The second two digits are the section, describing the relative position of the stadium
    game_data['block']= game_data['digit']-game_data['deck']*100
    
    return game_data


#For the second tier of the stadium, the rows are lettered, not numbered
#The letters are still relative positions, not categorical variables
#This code converts the letters into tnumbers such that A=1, B=2....

di=dict(zip(string.letters,[ord(c)%32 for c in string.letters]))

def convert_to_number (i):
    try:
       i= int(i)
    except:
        try:
           i= int(di[i])
        except:
            i= -42
    return i


#This function takes all the data observed for a given game
#It reads the data in and does some further processing
#It has two arguments, Event_ID: The stubhub of ID number for the event
#            dir_data: is the data to read

def try_int (num):
	try:
		return int(num) 
	except:
		return -42



def stack_game (event_id, dir_data, db_con):
    #This counts the number of files read in
    i=0
    #This lists all the files in the dir_data folder
    file_names = os.listdir(dir_data)
    #Loop through all the files in the folder.
    #If the file contains the Event_ID , It is read in and cleaned
    
    t_minus_min = 10^9
    
    for pickle in file_names:
        if pickle[:7]== str(event_id):
        	query_time= str(pickle[8:22])
        	game_time_data = pd.io.pickle.read_pickle('%s%s' %(dir_data, pickle))
        	game_time_data = clean_data(game_time_data)
        	sql_str = 'SELECT Event_ID, Year, Month, Day, Hour, Minute FROM event_char WHERE Event_ID = %d' %event_id
        	
        	event_char = sql.read_frame(sql_str , con=db_con )
        	
        	game_year = int(event_char['Year'])
        	game_month = int(event_char['Month'])
        	game_day = int(event_char['Day'])
        	game_hour = int(event_char['Hour'])
        	game_minute = int(event_char['Minute'])
        	
        	game_time_data.event_year = int(event_char['Year'])
        	game_time_data.event_month = int(event_char['Month'])
        	game_time_data.event_day = int(event_char['Day'])
        	game_time_data.event_hour = int(event_char['Hour'])
        	game_time_data.event_minute = int(event_char['Minute'])
        	
        	game_datatime =pd.datetime(game_year,game_month, game_day, game_hour, game_minute)
        	
        	
        	query_year= int(query_time[:2])+2000
        	query_month= int(query_time[3:5])
        	query_day= int(query_time[6:8])
        	query_hour= int(query_time[9:11])
        	query_minute= int(query_time[12:14])
        	query_datatime =pd.datetime(query_year,query_month, query_day, query_hour, query_minute)
        	t_minus = (game_datatime- query_datatime).total_seconds()//60
        	game_time_data['t_minus'] = t_minus
        	if t_minus > 0:
        		t_minus_min = t_minus if t_minus < t_minus_min else t_minus_min 
            	#If this is the first file read in, it becomes the basis for the final data
            	#Otherwise append 
            	if i==0:
                	all_game_time_data = game_time_data
            	else:
                	all_game_time_data = all_game_time_data.append(game_time_data)
            	i+=1
    all_game_time_data= all_game_time_data.reset_index(drop=True)
    all_game_time_data['last_timeobs']= (all_game_time_data.t_minus == t_minus_min)*1

    #This calculates the time from the query to the time time of the event
    
    #A small number of tickets have non-standard rows. These are filtered out
    # A small number of tickets are "Club Level" The Club level tickets are fare more expensive
    #than the rest of the sample are therefore filtered out
    all_game_time_data['row']=all_game_time_data['row'].apply(convert_to_number)
    all_game_time_data= all_game_time_data[all_game_time_data['row'] != -42]
    all_game_time_data= all_game_time_data[all_game_time_data['letter'] != 'CL']
 
    all_game_time_data['seat']=all_game_time_data['seat'].apply(try_int)
    all_game_time_data= all_game_time_data[all_game_time_data['seat'] != -42]    
    
    
    return all_game_time_data
	


