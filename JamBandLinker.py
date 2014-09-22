import praw
from praw.helpers import flatten_tree
import re

r = praw.Reddit('JamBandLinkerBot 1.0 by /u/DTKing')
subreddit = r.get_subreddit('grateful_dead')
submissionGenerator = subreddit.get_new(limit=20)

def fixStringLengths(toAppend):
	

	"""if ord(toAppend[0][0]) < 48 or ord(toAppend[0][0]) > 57:
		toAppend[0] = toAppend[0][1:] #remove the offending char we grabbed """
	
	if toAppend[0][0] == '0': #need to remove the 0 from the month
		toAppend[0].lstrip('0')

	if toAppend[1][0] == '0': #do the same for the days
		toAppend[1].lstrip('0')

	if len(toAppend[2]) == 2: #need to prepend '19' to this string
		toAppend[2] = '19' + toAppend[2]

	return toAppend

alreadyDone = set() #set to track if comment has already been analyzed
myComments = []
print "here!!!!!!"
#for submission in submissions:
#	flat_comments = praw.helpers.flatten_tree(submission.comments)
for submission in submissionGenerator:
	for comment in submission.comments:
		myComments.append(comment)
i = 1
print "here"
print "Number of comments parsed: " + str(len(myComments))
regexString = re.compile('\d{1,3}[-./]\d{1,2}[-./]\d{2,4}')
print "Comments flattened and regex string compiled"
for comment in myComments:
	search = regexString.search(comment.body) #search will contain the found date string\
	if search is not None and comment.id not in alreadyDone: #check for a date-like string that's new
		print search.group();
		toAppend = re.split('[-./]', search.group())
		for string in toAppend:
			print string

		if len(toAppend[0]) == 3: #we got a bad string
			continue

		if len(toAppend[0]) == 2:
			if ord(toAppend[0][0]) > 49 or ord(toAppend[0][0]) < 48: #first months digit can only be 0,1
				continue
			if ord(toAppend[0][1]) > 50 or ord(toAppend[0][1]) < 48: #second months digit can only be 0,1,2
				#print comment.body
				continue
		#toAppend[0] = toAppend[0].lstrip(' ')
		fixStringLengths(toAppend);
		
		''' comment.reply('Here\s a link to the mentioned show!\n' + 
					  '[' + search + ']' + '('
			          'www.relisten.net/grateful-dead/' + 
			           toAppend[2] + '/' toAppend[0] + '/' toAppend[1])	+ ')'	'''
		print comment.body
		alreadyDone.add(comment.id)

		print 'Here\'s a link to the mentioned show!' 
		print '[' + search.group() + ']' + '(' + 'http://www.relisten.net/grateful-dead/' 
		print toAppend[2] + '/' + toAppend[0] + '/' + toAppend[1] + ')'
	elif search is None:
		#print comment.body
		print "Search is none" + str(i)
		i = i+1
	elif comment.id in alreadyDone:
		print "Comment already here"
	else:
		print "confused" 


	