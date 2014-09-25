

#This function reads in a particular JSON file and creates a pd.DataFrame
#In the output data frame, each observation is one ticket at one point in time
#The dataframe contains out


def read_tickets (stubhub_file):

	#Load File
	data = json.load(urllib2.urlopen(url))
	tickets = data['eventTicketListing']['eventTicket']

    #Parse JSON file to geat ticket ID, seat info and price

    ticket_id = [ticket['id'] for ticket in tickets]
    ticket_section = [str(ticket['st'] )for ticket in tickets]
    ticket_row = [str(ticket['rd']) for ticket in tickets]
    ticket_qt= [str(ticket['qt']) for ticket in tickets]
    ticket_seat = [str(ticket['se']) for ticket in tickets]
    prices = [ticket['tc']['amount'] for ticket in tickets]
    
    
    #Each Stubhub Listing may have multiple tickets
    #This loops through the listing, to make a python list of the
    #the available tickets on a particular listing
    ticket_seats_list = []
    for seats in ticket_seat:
        seats = str(seats)
        seats =seats.split(",")
        ticket_seats_list.append(seats)
        

	#Create dictionary with data
    ticket_listing = {'id': ticket_id,
                      'section':ticket_section,
                      'row':ticket_row,
                      'price': prices,
                      'qt': ticket_qt ,
                        'seats': ticket_seats_list}

    
    #This function makes a pda.dataframe from the dictionary with data
    ticket_listing_frame = pd.DataFrame(ticket_listing)
    ticket_listing_frame.insert(0, 'query_time', current_time , allow_duplicates=False)
    ticket_listing_frame.insert(0, 'event_id', event_id , allow_duplicates=False)
    
    
    #In the above Data Frame, the variable "seats" is a nest list
    #This code transforms the the data to make it "long" by steat
    
    #s is a new python Series, with each list 
    s= ticket_listing_frame.seats.apply(pd.Series).unstack().reset_index(level=0, drop = True)
    s.name = 'seat'
    
    #This merges the python the new series with the information about the seas, from the old data fram
    out = ticket_listing_frame.drop('seats', axis = 1).join(s)
    
    #This merge create many NAs (it becomes long to the longest set of listed tickets
    #This removes the uncessary tickets
    out = out.dropna(subset=['seat'])
    out = out.reset_index(drop=True)
	
	return (out)
	