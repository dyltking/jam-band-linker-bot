import praw
import re
import httplib2
import sys

ASCII_ZERO = 48
ASCII_ONE = 49
ASCII_TWO = 50

def isHttpValid(day, month, year):
	requestString = "http://relisten.net/api/artists/grateful-dead/years/" + year + "/shows/" + year + "-"
		
	if len(month) == 1: #need to add a 0 onto the month for the requestString if it's not there already
		requestString = requestString + '0' + month
	else:
		requestString = requestString + month
	
	if len(day) == 1: #and the same for the day
		requestString = requestString + '-' + '0' + day
	else:
		requestString = requestString + '-' + day

	h = httplib2.Http()
	resp, content = h.request(requestString, 'HEAD')

	if int(resp['status']) >= 400:
		print "BAD DATE " + resp['status'] + '\n'
		return False
	else:
		return True



if len(sys.argv) < 2: #no command line input
	print "You need to specify a subreddit!"
	sys.exit()
elif len(sys.argv) >= 2: #a subreddit was specified
	subredditToCrawl = sys.argv[1]

r = praw.Reddit('JamBandLinkerBot 1.0 by /u/DTKing')
subreddit = r.get_subreddit(subredditToCrawl)
submissionGenerator = subreddit.get_new(limit = 10)

alreadyDone = set() #set to track if comment has already been analyzed

#Create a large list of comments
myComments = []
for submission in submissionGenerator:
	for comment in submission.comments:
		myComments.append(comment)
i = 1
print "Number of comments parsed: " + str(len(myComments)) + '\n'
regexString = re.compile('\d{1,3}[-./]\d{1,2}[-./]\d{2,4}')

for comment in myComments:
	if comment.id in alreadyDone: #check this early to skip unnecessary regex searching
		continue
	
	datesToPost = []
	linksToPost = []
	
	searchIterator = regexString.finditer(comment.body) #search will contain the found date string
	if searchIterator is not None:
		for search in searchIterator: #check for a date-like string that's new
			print search.group();
			
			toAppend = re.split('[-./]', search.group()) #split the search results into distinct indices

			#make the indices returned by our regex split nice to use
			year = toAppend[2]
			month = toAppend[0]
			day = toAppend[1]
			
			if len(month) == 3: #we got a bad string :'(
				continue

			if len(month) == 2: #if the months has two digits, validate
				if ord(month[0]) > ASCII_ONE or ord(month[0]) < ASCII_ZERO: #first months digit can only be 0,1
					continue
				if ord(month[0]) == ASCII_ONE: #if first month's digit is 1	
					if ord(month[1]) > ASCII_TWO or ord(month[1]) < ASCII_ZERO: #second months digit can only be 0,1,2
						continue

			#Fix string lengths for use in url creation
			if month[0] == '0': #need to remove the 0 from the month
				month = month.lstrip('0')

			if day[0] == '0': #do the same for the days
				day = day.lstrip('0')

			if len(year) == 2: #need to prepend '19' to the years
				year = '19' + year		

			#check if http request is valid, in case someone posted a date that the band didn't play
			if not isHttpValid(day, month, year):
				continue

			#print comment.body
			urlString = 'http://www.relisten.net/grateful-dead/' + year + '/' + month + '/' + day
			linksToPost.append(urlString) #add this string into our list of links to post
			datesToPost.append(search.group())

	elif searchIterator is None:
		#print comment.body
		print "Search is none" + str(i) + '\n'
		i = i+1
	
	elif comment.id in alreadyDone:
		print "Comment already here"
	
	else:
		print "confused" 

	#Manage printing of links
	if len(linksToPost) == 1:
		print 'Here\'s a link to the mentioned show!' 
		print '[' + datesToPost[0] + ']' + '(' + linksToPost[0] + ')' + '\n'
	elif len(linksToPost) > 1:
		i = 0
		print 'Here are links to the mentioned shows!'
		for link in linksToPost:
			print '[' + datesToPost[i] + ']' + '(' + link + ')'
			i += 1
		print ''

	alreadyDone.add(comment.id) #add this comment to our list of read comments

	