import os, argparse, smtplib, string, cPickle as pickle
from datetime import datetime, date, time, timedelta
from BeautifulSoup import BeautifulSoup
from urllib2 import urlopen


"""
usage: deecrawl2.py [-h] [-d] url

crawls a url passed as command line argument for job listings matching the
provided criteria.

positional arguments:
  url -- url to start crawl from

optional arguments:
  -h, --help  show this help message and exit
  -d, --dump  dumps and replaces existing dictionaries
"""

parser = argparse.ArgumentParser(
        description='crawls a url passed as command line argument for job \
        listings matching the provided criteria.', fromfile_prefix_chars="@" )
parser.add_argument('-d', '--dump', 
	 help='dumps and replaces existing dictionaries', action="store_true")
parser.add_argument('url', help='url to start crawl from', action='store')
args = parser.parse_args()

if args.dump: dump = True           # dump; will override any existing
else: dump = False                  # dictionaries and drop existing tables


daysBack = 7    # number ofdays to search back
match_strings = ['dental', 'hygiene', 'hygienist', 'dentist']
matchedJobs = {}
newMatches = {}

# ---------------------------------------------------------------------------- #
#   function - pickleDump
#   saves "files" and "extensions" dict to a file
# ---------------------------------------------------------------------------- #
def pickleDump():
  global matchedJobs
  print 'pickling...'
  pickle.dump( matchedJobs, open( "filesdict.p", "wb" ) )


# ---------------------------------------------------------------------------- #
#   function - pickleLoad
#   loads "files" and "extensions" dict from a file
# ---------------------------------------------------------------------------- #
def pickleLoad():
  global matchedJobs
  cwd = os.getcwd()
  fileDictPickle = str(cwd) + '/filesdict.p'
  print 'Loading files...'
  matchedJobs = pickle.load( open( fileDictPickle, "rb" ) )



# ---------------------------------------------------------------------------- #
#   function - pickleTry
#   checks if pickled files already exist
# ---------------------------------------------------------------------------- #
def pickleTry():
  cwd = os.getcwd()
  try:
    with open(cwd+'/filesdict.p') as f:
        pass
        print 'pickle found'
        return True
  except IOError as e:
    print 'pickle not found'
    return False

# dictionary selection
#  - if dump flag; replace existing dictionaries
#  - if pickle's found, use; else start new dictionaries
if not dump:
  if pickleTry():
      pickleLoad()
      print 'Using existing dictionary...\n'
  else:
      print 'Starting new dictionary...'
else:
  if pickleTry():
      'Replacing existing dictionaries.'


def matched(celldata = None):
    in_range = False
    # handling string for now but would be easy to add ranges for ints
    if celldata != None:
        celldata = celldata.lower()
        if any(word in celldata for word in match_strings):
            in_range = True
    return in_range

def dateRange(ban_date = None, delta = 5):
	today = datetime.today()
	margin = timedelta(days=delta)
	if date != None:
		# ex: Fri May 17
		fmtdate = datetime.strptime(ban_date, '%a %b %d')
		fmtdate = fmtdate.replace(year = today.year)
		print fmtdate - today

		if today - fmtdate > margin:
			return False		# too old
		else:
			return True			# within range
		return False

def getText(string = None):
	if string != None:
		try:
			closeBkt = string.index('>') + len('>')
			openBkt  = string.index('<', closeBkt)
			return string[closeBkt:openBkt]
		except ValueError:
			return ""

def getPostInfo(pid = 0, postUrl = None):

	if postUrl != None:
		postUrl = args.url[:-5] + postUrl
		postTable = BeautifulSoup(urlopen(postUrl))
		postDate = postTable.date
		replytext = postTable.find('section', attrs={'class' : 'dateReplyBar'})
		postReplyEmail = replytext.a['href']
		postTitle = postTable.find('h2', attrs={'class' : 'postingtitle'})
		postBody = postTable.find('section', attrs={'id' : 'postingbody'})
		postBlurbs = postTable.find('ul', attrs={'class' : 'blurbs'})

		if pid not in matchedJobs:
			matchedJobs[pid] = [postUrl, postDate, postReplyEmail, postTitle, \
								postBody, postBlurbs]
			newMatches[pid] = [postUrl, postDate, postReplyEmail, postTitle, \
							   postBody, postBlurbs]

def send_email(email_body = None):

    from_addr    = os.environ.get('FROM_ADDR') 
    to_addr_list = [os.environ.get('TO_ADDR')]
    cc_addr_list = [os.environ.get('CC_ADDR')]
    subject      = 'Howdy'
    # message      = 'Howdy from a python function'
    message 	 = email_body 
    login        = os.environ.get('EMAIL_LOGIN')
    password     = os.environ.get('EMAIL_PASSWD')
    smtpserver   = 'smtp.gmail.com:587'

    header  = 'From: %s\n' % from_addr
    header += 'To: %s\n' % ','.join(to_addr_list)
    header += 'Cc: %s\n' % ','.join(cc_addr_list)
    header += 'Subject: %s\n\n' % subject
    message = header + message

    try:
        server = smtplib.SMTP(smtpserver)
        server.starttls()
        server.login(login,password)
        server.sendmail(from_addr, to_addr_list, message)
        server.quit()
        print 'successfully sent the mail'
    except Exception, e:
        print "Unable to send email. Error: %s" % str(e)


urls = [args.url]

site = urls.pop()
table = BeautifulSoup(urlopen(site))

if table.find('p', attrs={'class' : 'nextpage'}):
	nextpage = table.find('p', attrs={'class' : 'nextpage'})
	nexturl = args.url + str(nextpage.find('a').get('href'))
	urls.append(nexturl)
	print nexturl

# get first date in soup
	postsdate = table.find('h4', attrs={'class' : 'ban'})
	# ex: <h4 class="ban">Fri May 17</h4>
	pdate = getText(str(postsdate))
	print pdate


while len(urls) > 0 and dateRange(pdate, daysBack):

	rows = table.findAll('p', attrs={'class' : 'row'})

	for row in rows:
		pid = row['data-pid']
		span = row.find('span', attrs={'class' : 'pl'})
		title = span.find('a')
		if matched(getText(str(title))):
			print pid, getText(str(title))
			postUrl = title['href']
			getPostInfo(pid, postUrl)

	# prompt = raw_input('press any key to continue')

	site = urls.pop()
	table = BeautifulSoup(urlopen(site))

# get next url and append to urls
	if table.find('p', attrs={'class' : 'nextpage'}):
		nextpage = table.find('p', attrs={'class' : 'nextpage'})
		nexturl = args.url + str(nextpage.find('a').get('href'))
		urls.append(nexturl)
		print nexturl

# get next date in soup
	postsdate = table.find('h4', attrs={'class' : 'ban'})
	# ex: <h4 class="ban">Fri May 17</h4>
	pdate = getText(str(postsdate))
	print pdate

# print dictionary of jobs
if len(newMatches) > 0:
	numOfNewMatches = len(newMatches)

	email_body = str(numOfNewMatches) + '\n'

# [postUrl, postDate, postReplyEmail, postTitle, postBody, postBlurbs]
	for key, value in newMatches.iteritems():
		email_body += str(value[3])[52:-5].strip('\n')
		email_body += '\n' + str(value[0])
		email_body += '\n'

	send_email(email_body)

print 'storing pickle'
pickleDump()


