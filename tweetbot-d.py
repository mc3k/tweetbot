#!/usr/bin/env python
import sys, os, logging, urllib
import xml.etree.ElementTree
from twython import TwythonStreamer, Twython
from daemon3x import daemon

# Logging
logging.basicConfig(filename='tweetbot.log',
                            filemode='a',
							format='[%(asctime)s] %(message)s',
							datefmt='%Y/%m/%d %H:%M:%S',
                            level=logging.INFO)

# Twitter API keys
CONSUMER_KEY = 'xxxxxxxxxxxxxxxxxxxxxxxxx'
CONSUMER_SECRET = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
ACCESS_KEY = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
ACCESS_SECRET = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

# Wolfram|Alpha API Key
appid = 'xxxxxxxxxxxxxxxxx'

# Your twitter handle (with @ symbol)
TERMS = '@twitter_handle'

# Superuser twitter handle (without @)
superuser = 'twitter_handle'

def fetchanswer( engine, query, appid ):
	if engine== 'wolfram':
		element = 'plaintext'
		cmd = 'curl -s "http://api.wolframalpha.com/v2/query?appid='+appid+'&format=plaintext&podindex=2&input='+query+'"'
		logging.info('WOLF : '+query)
	elif engine == 'wikipedia':
		element = 'extract'
		cmd = 'curl -s "http://en.wikipedia.org/w/api.php?action=query&prop=extracts&format=xml&exchars=140&exintro=&explaintext=&exsectionformat=plain&titles='+query+'&redirects="'
		logging.info('WIKI : '+query)
	line = os.popen(cmd).read()
	root = xml.etree.ElementTree.fromstring(line)
	output = ""
	for neighbor in root.iter(element):
		if neighbor.text is not None:
			output = output+neighbor.text
	return output

def fetchtemp():
	cmd = '/opt/vc/bin/vcgencmd measure_temp'
	line = os.popen(cmd).readline().strip()
	output = line.split('=')[1].split("'")[0]+' C'
	return output
	
def fetchuptime():
	cmd = 'uptime'
	line = os.popen(cmd).readline().strip()
	output = line.split('up ')[1].split(",")[0]
	return output
	
# Setup callbacks from Twython Streamer
class MyStreamer(TwythonStreamer):
	def on_success(self, data):
		if 'text' in data:

			logging.info('RECD : '+data['user']['screen_name']+": "+data['text'])
			api = Twython(CONSUMER_KEY,CONSUMER_SECRET,ACCESS_KEY,ACCESS_SECRET) 		
			msg = data['text']
			user = data['user']['screen_name']
			msg = msg.replace(TERMS, '')
			
			if msg.find('#stoptweeting') != -1:
				msg = msg.replace('#stoptweeting', '')
				if user == superuser:
					output = ' stopping tweeting'
					api.update_status(status='@'+user+output, in_reply_to_status_id=data['id_str'])
					logging.info('SENT : @'+user+output)
					logging.info('Disconnecting')
					self.disconnect()
					daemonx.stop()
				
			if msg.find('#cputemp') != -1:
				msg = msg.replace('#cputemp', '')
				output = ' cpu temp is currently '+fetchtemp()
				api.update_status(status='@'+user+output, in_reply_to_status_id=data['id_str'])
				logging.info('SENT : @'+user+output)
				
			if msg.find('#uptime') != -1:
				msg = msg.replace('#uptime', '')
				output = ' my uptime is '+fetchuptime()
				api.update_status(status='@'+user+output, in_reply_to_status_id=data['id_str'])
				logging.info('SENT : @'+user+output)
				
			if msg.find('#question') != -1:
				searchterm = urllib.parse.quote_plus(msg.replace('#question','').strip())
				output = fetchanswer('wolfram',searchterm,appid)
				if output == '':
					output = fetchanswer('wikipedia',searchterm,appid)
				if output == '': 
					output = 'null'
				if output != 'null':
					api.update_status(status='@'+user+' '+output, in_reply_to_status_id=data['id_str'])
					logging.info('SENT : @'+user+' '+output)
				
	def on_error(self, status_code, data):
		logging.info('ERROR : ',status_code, data)

class MyDaemon(daemon):
	def run(self):
		while True:
			logging.info('--------------')
			logging.info('Daemon Started')
			# Requires Authentication as of Twitter API v1.1
			stream = MyStreamer(CONSUMER_KEY,CONSUMER_SECRET,ACCESS_KEY,ACCESS_SECRET)
			stream.statuses.filter(track=TERMS)
			logging.info('Daemon Ended')

if __name__ == "__main__":
        daemonx = MyDaemon('/tmp/daemon-tweetbot.pid')
        if len(sys.argv) == 2:
                if 'start' == sys.argv[1]:
                        daemonx.start()
                elif 'stop' == sys.argv[1]:
                        logging.info('Daemon stopped')
                        daemonx.stop()
                elif 'restart' == sys.argv[1]:
                        logging.info('Daemon restarting')
                        daemonx.restart()
                else:
                        print("Unknown command")
                        sys.exit(2)
                sys.exit(0)
        else:
                print("usage: %s start|stop|restart" % sys.argv[0])
                sys.exit(2)
