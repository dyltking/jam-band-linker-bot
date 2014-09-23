import praw
import re
import httplib2


def fixStringLengths(toAppend):
	if toAppend[0][0] == '0': #need to remove the 0 from the month
		toAppend[0].lstrip('0')

	if toAppend[1][0] == '0': #do the same for the days
		toAppend[1].lstrip('0')

	if len(toAppend[2]) == 2: #need to prepend '19' to this string
		toAppend[2] = '19' + toAppend[2]

	return toAppend


r = praw.Reddit('JamBandLinkerBot 1.0 by /u/DTKing')
subreddit = r.get_subreddit('gdbot_test')
submissionGenerator = subreddit.get_new(limit=5)

alreadyDone = set() #set to track if comment has already been analyzed
myComments = []
#Create a large list of comments
for submission in submissionGenerator:
	for comment in submission.comments:
		myComments.append(comment)
i = 1
print "Number of comments parsed: " + str(len(myComments))
regexString = re.compile('\d{1,3}[-./]\d{1,2}[-./]\d{2,4}')

for comment in myComments:
	search = regexString.search(comment.body) #search will contain the found date string\
	if search is not None and comment.id not in alreadyDone: #check for a date-like string that's new
		print search.group();
		toAppend = re.split('[-./]', search.group())
		for string in toAppend:
			print string

		if len(toAppend[0]) == 3: #we got a bad string :'(
			continue

		if len(toAppend[0]) == 2:
			if ord(toAppend[0][0]) > 49 or ord(toAppend[0][0]) < 48: #first months digit can only be 0,1
				continue
			if ord(toAppend[0][1]) > 50 or ord(toAppend[0][1]) < 48: #second months digit can only be 0,1,2
				continue

		fixStringLengths(toAppend);
		year = toAppend[2]
		month = toAppend[0]
		day = toAppend[1]
		urlString = 'http://www.relisten.net/grateful-dead/' + year + '/' + month + '/' + day

		requestString = "http://relisten.net/api/artists/grateful-dead/years/" + year + "/shows/" + year + "-"
		
		if len(month) == 1: #need to add a 0 onto the month for the requestString if it's not there already
			requestString = requestString + '0' + month
		else:
			requestString = requestString + month
		
		if len(day) == 1: #and the same for the day
			requestString = requestString + '-' + '0' + day
		else:
			requestSTring = requestString + '-' + day

		h = httplib2.Http()
		resp, content = h.request(requestString, 'HEAD')
	
		if int(resp['status']) >= 400:
			print "BAD DATE " + resp['status']
			continue
		''' comment.reply('Here\s a link to the mentioned show!\n' + 
					  '[' + search + ']' + '(' + urlString + ')'
			          	'''
		print comment.body
		alreadyDone.add(comment.id)

		print 'Here\'s a link to the mentioned show!' 
		print '[' + search.group() + ']' + '(' + 'http://www.relisten.net/grateful-dead/' + year + '/' + month + '/' + day + ')'
	elif search is None:
		#print comment.body
		print "Search is none" + str(i)
		i = i+1
	elif comment.id in alreadyDone:
		print "Comment already here"
	else:
		print "confused" 


	