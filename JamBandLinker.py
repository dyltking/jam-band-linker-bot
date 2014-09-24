import praw
import re
import httplib2
import sys
import time

ASCII_ZERO = 48
ASCII_ONE = 49
ASCII_TWO = 50

#Ping the relisten.net api to see if the prospective URL is valid (effectively, checks to see if the band played this date)
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

#Check if a comment was made by this bot, or has already been replied to by this bot
def repliedAlready(comment):
	if str(comment.author) == 'JamBandLinkerBot': #Don't reply to myself!
		return True

	for reply in comment.replies:
		if str(reply.author) == 'JamBandLinkerBot': #If I've already responded to this comment, skip it
			return True

	return False


#Manage posting of comments, including rate limit logic
def postReplies(linksToPost, datesToPost):
	if len(linksToPost) == 1: #Only one valid date in original comment
		try:
			comment.reply( 'Here\'s a link to the mentioned show!\n\n' + 
			'[' + datesToPost[0] + ']' + '(' + linksToPost[0] + ')')
			print "Replied to a comment for date " + datesToPost[0] + "."

		except praw.errors.RateLimitExceeded as error:
			print("RateLimit: {:f} seconds".format(error.sleep_time))
			time.sleep(error.sleep_time)
			comment.reply( 'Here\'s a link to the mentioned show!\n\n' + #comment after having waited for Rate Limit to expire
			'[' + datesToPost[0] + ']' + '(' + linksToPost[0] + ')')
			print "Replied to a comment for date " + datesToPost[0] + "."

	elif len(linksToPost) > 1: #Multiple valid dates in original comment
		index = 0
		commentString = 'Here are links to the mentioned shows!' #Have to build this string
		for link in linksToPost:
			commentString += '\n\n[' + datesToPost[index] + ']' + '(' + link + ')'
			index += 1
		try:
			comment.reply( commentString )
			print "Replied to a multidate comment."

		except praw.errors.RateLimitExceeded as error:
			print("RateLimit: {:f} seconds".format(error.sleep_time))
			time.sleep(error.sleep_time)
			comment.reply( commentString ) #comment after having waited for Rate Limit to expire
			print "Replied to a multidate comment."


if len(sys.argv) < 2: #no command line input
	print "You need to specify a subreddit!"
	sys.exit()
elif len(sys.argv) >= 2: #a subreddit was specified
	subredditToCrawl = sys.argv[1]

r = praw.Reddit('JamBandLinkerBot 1.0 by /u/DTKing')
r.login() #login using local praw.ini config
subreddit = r.get_subreddit(subredditToCrawl)
submissionGenerator = subreddit.get_new(limit = 25)

alreadyDone = set() #set to track if comment has already been analyzed, probably superfluous

#Create a large list of comments
myComments = []
for submission in submissionGenerator:
	submission.replace_more_comments(None, 1) #Replace MoreComments objects with Comment objects
	allComments = praw.helpers.flatten_tree(submission.comments) #flatten the comment tree into one list for easy iteration
	for comment in allComments:
		myComments.append(comment)
i = 1
print "Number of comments parsed: " + str(len(myComments)) + '\n'
regexString = re.compile('\d{1,3}[-./]\d{1,2}[-./]\d{2,4}')

for comment in myComments:
	if comment.id in alreadyDone or repliedAlready(comment): #check these early to skip unnecessary regex searching
		print "Skipping this comment, I already replied to it or it's my comment."
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

			urlString = 'http://www.relisten.net/grateful-dead/' + year + '/' + month + '/' + day
			linksToPost.append(urlString) #add this string into our list of links to post
			datesToPost.append(search.group())

	elif searchIterator is None:
		print "Search is none" + str(i) + '\n'
		i = i+1
	
	elif comment.id in alreadyDone:
		print "Comment already here"
	
	else:
		print "?!?!?!??!?!?!?!" 

	postReplies(linksToPost, datesToPost) #make posts!

	alreadyDone.add(comment.id) #add this comment to our list of read comments
	
print "Finished execution of script!"	