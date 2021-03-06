import praw
import re
import httplib2
import sys
import time


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
      '[' + datesToPost[0] + ']' + '(' + linksToPost[0] + ')' + '\n\n^^This ^^bot ^^was ^^made ^^by ^^/u/DTKing. ' + 
      '^^Please ^^message ^^him ^^with ^^any ^^questions, ^^comments, ^^or ^^concerns ^^you ^^may ^^have.')

    except praw.errors.RateLimitExceeded as error: #ran into a rate limit, wait the specified time then reply
      print("RateLimit: {:f} seconds".format(error.sleep_time))
      time.sleep(error.sleep_time)
      comment.reply( 'Here\'s a link to the mentioned show!\n\n' + #comment after having waited for Rate Limit to expire
      '[' + datesToPost[0] + ']' + '(' + linksToPost[0] + ')' + '\n\n^^This ^^bot ^^was ^^made ^^by ^^/u/DTKing. ' + 
      '^^Please ^^message ^^him ^^with ^^any ^^questions, ^^comments, ^^or ^^concerns ^^you ^^may ^^have.')

    finally: 
      print "Comment #" + str(commentIndex) + ": Replied to a comment for date " + datesToPost[0] + "!"
      return 1


  elif len(linksToPost) > 1: #Multiple valid dates in original comment
    index = 0
    commentString = 'Here are links to the mentioned shows!' #Have to build this string before posting
    for link in linksToPost:
      commentString += '\n\n[' + datesToPost[index] + ']' + '(' + link + ')'
      index += 1
    commentString += '\n\n^^This ^^bot ^^was ^^made ^^by ^^/u/DTKing. '
    commentString += '^^Please ^^message ^^him ^^with ^^any ^^questions, ^^comments, ^^or ^^concerns ^^you ^^may ^^have.'
    
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
  regexString = re.compile('\[?\s*\d{1,3}[-./]\d{1,2}[-./]\d{2,4}(?!])') #Look for a string that resembles a date, but not already a link
  commentIndex = 0
  postCounter = 0

  #For each comment in our list, analyze, test, and potentially post a reply to it
  for comment in myComments:

    commentIndex += 1
    if comment.id in alreadyDone or repliedAlready(comment): #check these early to skip unnecessary regex searching
      print "Comment #" + str(commentIndex) + ": Already replied to this, or it's my own comment."
      continue
    #We'll use these to gather any valid dates (and their corresponding links) that we need to reply to
    datesToPost = []
    linksToPost = []
    
    searchIterator = regexString.finditer(comment.body) #search will contain the found date string

    badRequestAlready = False #to ensure the bad HTTP request message is only printed once per comment
    emptyIterator = True #to check if the iterator was empty or not
    alreadyLinked = False #to ensure the OP already linked message is only printed once per comment
    
    for search in searchIterator: #check for a date-like string that's new
      emptyIterator = False #toggle this to signal that the iterator wasn't empty
      

      toAppend = re.split('[-./]', search.group()) #split the search results into distinct indices

      #Make the indices returned by our regex split nice to use
      year = toAppend[2]
      month = toAppend[0]
      day = toAppend[1]
      
      #Fix string lengths for use in url creation
      if month[0] == '[': #the OP of this comment probably already linked something here, so we want to continue
        if not alreadyLinked: 
          print "Comment #" + str(commentIndex) + ": OP already linked one or more dates." #post a diagnostic message
        alreadyLinked = True #toggle this so this diagnostic message is only printed once per comment
        continue

      #need to remove the 0 from the month, and any potential spaces or newlines gathered
      month = month.lstrip("\n0 ")

      if day[0] == '0': #do the same for the days
        day = day.lstrip('0')

      if len(year) == 2: #need to prepend '19' to the years
        year = '19' + year    

      #Check if the band actually played this date via making a request to the streaming service
      if not isHttpValid(day, month, year):
        if not badRequestAlready:
          print "Comment #" + str(commentIndex) + ": Bad HTTP request(s)."
        badRequestAlready = True #toggle this so this diagnostic message only gets printed once per comment
        continue

      urlString = 'http://relisten.net/grateful-dead/' + year + '/' + month + '/' + day

      if urlString in linksToPost:
        continue
        
      linksToPost.append(urlString) #add this string into our list of links to post
      datesToPost.append(search.group().strip())

    if emptyIterator: #if the iterator was empty
      print "Comment #" + str(commentIndex) + ": No dates in this comment."

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
  return postCounter #return however many posts made on this iteration
  
  
#Parse and handle command line input, call the script with correct arguments
def main():
  postLimit = 0
  iterCounter = 0
  postCounter = 0
  if len(sys.argv) < 2: #no command line input
    print "You need to specify a subreddit!"
  
  elif len(sys.argv) == 2: #subreddit specified, no post limit specified. 
    subredditToCrawl = sys.argv[1]    
    while(True):
      iterCounter = iterCounter + 1
      
      try:
        postCounter = postCounter + jamBandLinker(subredditToCrawl, 0) #setting limit to 0 will use the account's default 
      except Exception:
        print "Exception caught."
        
      print "\nIteration " + str(iterCounter) + " finished."
      print "Total posts made: " + str(postCounter) + "."
      print "\nSleeping for 15 minutes.\n"
      time.sleep(900)
  
  elif len(sys.argv) >= 3: #a subreddit and post limit was specified
    subredditToCrawl = sys.argv[1]
    postLimit = sys.argv[2]
    while(True):
      iterCounter = iterCounter + 1

      try:
        jamBandLinker(subredditToCrawl, postLimit) #run the script!
      except Exception:
        print "Exception caught."
        
      print "\nIteration " + str(iterCounter) + " finished."
      print "Total posts made: " + str(postCounter) + "."
      print "\nSleeping for 15 minutes.\n"
      time.sleep(900)

if __name__ == '__main__':
  sys.exit(main())