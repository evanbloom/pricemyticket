from BeautifulSoup import BeautifulSoup
import urllib2
url="http://projects.propublica.org/docdollars/search?utf8=%E2%9C%93&term=&state%5Bid%5D=5&company%5Bid%5D=31&period%5B%5D=2012&services%5B%5D="
page=urllib2.urlopen(url)
soup = BeautifulSoup(page.read())

data = []
info = []
table = soup.find('table', attrs={'id':'payments_list'})
table_body = table.find('tbody')

rows = table_body.findAll('tr')
for row in rows:
    cols = row.findAll('td')
    info = []
    for item in cols:
    	cols = item.text.strip().encode('utf-8')
    	info.append(cols)
    data.append(info)

print data