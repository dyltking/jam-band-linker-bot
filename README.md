## JamBandLinkerBot.py

My go at a robust Reddit bot. 

This bot was made to analyze comments on any subreddit dedicated to a [jamband](http://en.wikipedia.org/wiki/Jam_band).  Specific concert dates are very important and often referenced in discussion on these subreddits.  The bot will parse new comments for valid dates and post a reply from /u/JamBandLinkerBot with a link to a stream of the specific concert.

To create this bot, I utilized [PRAW](http://praw.readthedocs.org/en/latest/index.html), as well as [httplib2](https://github.com/jcgregorio/httplib2). The bot will take in a subreddit as its first command line argument.  Optionally, a second command line argument may be used to specify how many top-level comments (and their replies) the bot should analyze.  


An example of how to run the bot looks like this:

`
python JamBandLinker.py grateful_dead 50
`

Made originally for [/r/grateful_dead](http://www.reddit.com/r/grateful_dead), but with possible future use on other jamband subreddits in mind.
