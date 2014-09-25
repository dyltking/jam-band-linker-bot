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
#Returns 1 for posted comment, 0 for no comment posted
def postReplies(comment, commentIndex, linksToPost, datesToPost):
	if len(linksToPost) == 1: #Only one valid date in original comment
		try:
			comment.reply( 'Here\'s a link to the mentioned show!\n\n' + 
			'[' + datesToPost[0] + ']' + '(' + linksToPost[0] + ')')

		except praw.errors.RateLimitExceeded as error: #ran into a rate limit, wait the specified time then reply
			print("RateLimit: {:f} seconds".format(error.sleep_time))
			time.sleep(error.sleep_time)
			comment.reply( 'Here\'s a link to the mentioned show!\n\n' + #comment after having waited for Rate Limit to expire
			'[' + datesToPost[0] + ']' + '(' + linksToPost[0] + ')')

		finally: 
			print "Comment #" + str(commentIndex) + ": Replied to a comment for date " + datesToPost[0] + "!"
			return 1


	elif len(linksToPost) > 1: #Multiple valid dates in original comment
		index = 0
		commentString = 'Here are links to the mentioned shows!' #Have to build this string before posting
		for link in linksToPost:
			commentString += '\n\n[' + datesToPost[index] + ']' + '(' + link + ')'
			index += 1

		try:
			comment.reply( commentString )

		except praw.errors.RateLimitExceeded as error: #ran into a rate limit, wait the specified time then reply
			print("RateLimit: {:f} seconds".format(error.sleep_time))
			time.sleep(error.sleep_time)
			comment.reply( commentString ) #comment after having waited for Rate Limit to expire

		finally:
			print "Comment #" + str(commentIndex) + ": Replied to a multidate comment!"
			return 1

	return 0


def validateStrings(day, month, year):
	if len(month) == 3: #we got a bad string :'(
		return False

	if len(month) == 2: #if the months has two digits, validate
		if ord(month[0]) > ASCII_ONE or ord(month[0]) < ASCII_ZERO: #first months digit can only be 0,1
			return False
		if ord(month[0]) == ASCII_ONE: #if first month's digit is 1	
			if ord(month[1]) > ASCII_TWO or ord(month[1]) < ASCII_ZERO: #second months digit can only be 0,1,2
				return False

	return True #All good!


#Script entry point
def jamBandLinker(subredditToCrawl, postLimit):
	r = praw.Reddit('JamBandLinkerBot 1.0 by /u/DTKing')
	r.login() #login using local praw.ini config
	subreddit = r.get_subreddit(subredditToCrawl)
	submissionGenerator = subreddit.get_new(limit = int(postLimit))

	alreadyDone = set() #set to track if comment has already been analyzed, probably superfluous

	#Create a large list of comments
	#Won't grab replies that are more than 10 levels deep, seems to be an issue with reddit api or a limitation of praw
	myComments = []
	
	print "Gathering comments..."
	
	#Gather comments into a list with which to iterate over
	for submission in submissionGenerator:
		submission.replace_more_comments(None, 1) #Replace MoreComments objects with Comment objects
		submissionComments = praw.helpers.flatten_tree(submission.comments) #flatten the comment tree into one list for easy iteration
		for comment in submissionComments:
			myComments.append(comment) 
	
	print "Done gathering comments!"
	print "Number of comments parsed: " + str(len(myComments)) + '\n'
	regexString = re.compile('\d{1,3}[-./]\d{1,2}[-./]\d{2,4}')
	commentIndex = 0
	postCounter = 0

	#For each comment in our list, analyze, test, and potentially post a reply to it
	for comment in myComments:
		commentIndex += 1
		if comment.id in alreadyDone or repliedAlready(comment): #check these early to skip unnecessary regex searching
			print "Comment #" + str(commentIndex) + ": Skipping this comment, I already replied to it or it's my comment."
			continue

		datesToPost = []
		linksToPost = []
		
		searchIterator = regexString.finditer(comment.body) #search will contain the found date string
		if searchIterator is not None:
			for search in searchIterator: #check for a date-like string that's new
				
				toAppend = re.split('[-./]', search.group()) #split the search results into distinct indices

				#Make the indices returned by our regex split nice to use
				year = toAppend[2]
				month = toAppend[0]
				day = toAppend[1]
				
				#Check if strings are valid calendar dates
				if not validateStrings(day, month, year):
					print "Comment #" + str(commentIndex) + ": Invalid string lengths or values."
					continue

				#Fix string lengths for use in url creation
				if month[0] == '0': #need to remove the 0 from the month
					month = month.lstrip('0')

				if day[0] == '0': #do the same for the days
					day = day.lstrip('0')

				if len(year) == 2: #need to prepend '19' to the years
					year = '19' + year		

				#Check if the band actually played this date via making a request to the streaming service
				if not isHttpValid(day, month, year):
					print "Comment #" + str(commentIndex) + ": Bad HTTP request."
					continue

				urlString = 'http://www.relisten.net/grateful-dead/' + year + '/' + month + '/' + day
				linksToPost.append(urlString) #add this string into our list of links to post
				datesToPost.append(search.group())

		elif searchIterator is None:
			print "Comment #" + str(commentIndex) + ": No dates in this comment."
		
		elif comment.id in alreadyDone:
			print "Comment #" + str(commentIndex) + ": Comment already in reviewed collection."
		
		else:
			print "Comment #" + str(commentIndex) + ": Not sure what happened here." 

		postCounter += postReplies(comment, commentIndex, linksToPost, datesToPost) #make posts!

		alreadyDone.add(comment.id) #add this comment to our list of read comments

	#Print how many comments we posted and indicate that we finished running the script
	print ''

	if postCounter == 0:
		print "Posted no new comments."
	elif postCounter == 1:
		print "Posted 1 new comment!"
	elif postCounter > 1:
 		print "Posted " + str(postCounter) + " new comments!"
	
	print "Finished execution of script!"	


#Parse and handle command line input, call the script with correct arguments
def main():
	if len(sys.argv) < 2: #no command line input
		print "You need to specify a subreddit!"
	elif len(sys.argv) == 2: #subreddit specified, no post limit specified. 
		subredditToCrawl = sys.argv[1]
		jamBandLinker(subredditToCrawl, 0) #setting limit to 0 will use the account's default (25 for unauthenticated users)
	elif len(sys.argv) >= 3: #a subreddit and post limit was specified
		subredditToCrawl = sys.argv[1]
		postLimit = sys.argv[2]
		jamBandLinker(subredditToCrawl, postLimit) #run the script!


if __name__ == '__main__':
	sys.exit(main())