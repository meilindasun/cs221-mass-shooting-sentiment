# -*- coding: utf-8 -*-
# Our code to scrape tweets from Twitter filtering by keyword and start and end date
# The logic interpreting json response received from the web in getTweets is based on Jefferson-Henrique's code cited in our report 
# Lara Bagdasarian and Meilinda Sun
import os
import datetime, time 
import urllib
from urllib import *
from urllib.parse import quote
import pandas as pd
from nltk.stem.snowball import SnowballStemmer
import string
import re
import json
import codecs
import http.cookiejar as cookielib
try:
    from http.cookiejar import CookieJar
except ImportError:
    from cookielib import CookieJar
import nltk
from pyquery import PyQuery

nltk.download("stopwords")
from nltk.corpus import stopwords
STOPWORDS = set(stopwords.words('english'))

from langdetect import detect

# Parse tweet before writing to CSV
def clean_text(text): 
    ## Remove puncuation
    text = text.translate(string.punctuation)
    ## Convert words to lower case and split them
    text = text.lower().split()
    ## Remove stop words and words beginning with '@'
    stops = set(stopwords.words("english"))
    text = [w for w in text if not w in stops and w[0] != '@' and len(w) >= 3]
    text = " ".join(text)
    ## Clean the text
    text = re.sub(r'^https?:\/\/.*[\r\n]*', '', text, flags=re.MULTILINE)
    text = re.sub(r"[^A-Za-z0-9^,!.\/'+-=]", " ", text)
    text = re.sub(r"what's", "what is ", text)
    text = re.sub(r"\'s", " ", text)
    text = re.sub(r"\'ve", " have ", text)
    text = re.sub(r"n't", " not ", text)
    text = re.sub(r"i'm", "i am ", text)
    text = re.sub(r"\'re", " are ", text)
    text = re.sub(r"\'d", " would ", text)
    text = re.sub(r"\'ll", " will ", text)
    text = re.sub(r"http", " ", text)
    text = re.sub(r"https", " ", text)
    text = re.sub(r",", " ", text)
    text = re.sub(r"\.", " ", text)
    text = re.sub(r"!", " ! ", text)
    text = re.sub(r"\/", " ", text)
    text = re.sub(r"\^", " ^ ", text)
    text = re.sub(r"\+", " + ", text)
    text = re.sub(r"\-", " - ", text)
    text = re.sub(r"\=", " = ", text)
    text = re.sub(r"'", " ", text)
    text = re.sub(r":", " ", text)
    text = re.sub(r"=", " ", text)
    text = re.sub(r"-", " ", text)
    text = re.sub(r"(\d+)(k)", r"\g<1>000", text)
    text = re.sub(r":", " : ", text)
    text = re.sub(r" e g ", " eg ", text)
    text = re.sub(r" b g ", " bg ", text)
    text = re.sub(r" u s ", " american ", text)
    text = re.sub(r"\0s", "0", text)
    text = re.sub(r" 9 11 ", "911", text)
    text = re.sub(r"e - mail", "email", text)
    text = re.sub(r"j k", "jk", text)
    text = re.sub(r"\s{2,}", " ", text)
    ## Stemming
    text = text.split()
    stemmer = SnowballStemmer('english')
    stemmed_words = [stemmer.stem(word) for word in text]
    text = " ".join(stemmed_words)
    return text

inds = []
# ind 0 represents the first 4pm subsequent to the event
date1 = datetime.datetime(2015, 11, 27)
date2 = datetime.datetime(2015, 11, 28)

start_time = []
end_time = []
# Change for other shootings
query_term = "Bernardino"
queryid = "bernardino"
for i in range(-5,60,1):
	inds.append(i)
	print(i)
	date1 += datetime.timedelta(days=1)
	date2 += datetime.timedelta(days=1)
	myday1 = date1.day
	myday2 = date2.day
	if len(str(myday1)) == 1:
		myday1 = '0' + str(myday1)
	if len(str(myday2)) == 1:
		myday2 = '0' + str(myday2)
	mystr1 = '%(year)s-%(month)s-%(day)s' % {"year": date1.year, "month": date1.month, "day": myday1}
	mystr2 = '%(year)s-%(month)s-%(day)s' % {"year": date2.year, "month": date2.month, "day": myday2}
	start_time.append(mystr1)
	end_time.append(mystr2)

# Postprocess output csv
def preprocCSV(filename):
	fp = pd.read_csv(filename, encoding = "ISO-8859-1", nrows=900, header=None, sep='\n')
	fp = fp[0].str.split(';', expand=True)
	prevegastweets = []
	prevegasembeddings = []
	count = 1

	newname = filename[:-7] + "300.csv"
	print(newname)

	f = open(newname, "w")
	c = 0
	for _, line in fp.iterrows():
	    if c == 0:
	      c = 1
	      continue
	    if count > 300:
	      break
	    try:
	        tweetText = line[4].replace('\n', ' ')
	        if detect(tweetText)=='en':
	        	tweetText = re.sub(r'(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?«»“”‘’]))', '', tweetText)
	        	tweetText = tweetText.replace('"','')
	        	tweetText = tweetText.replace(';',' ')
	        	tweetText = tweetText.replace(',','')
	        	f.write(tweetText)
	        	f.write('\n')
	        	count += 1
	        if count % 50 == 0:
	          print(str(count))
	    except:
	        pass
	print(count)
	f.close()
	TEST_DATA_DIR = newname
	test_df = pd.read_csv(TEST_DATA_DIR, encoding ='ISO-8859-1', usecols=[0], names=['text'], error_bad_lines=False)
	cleaned_test_df = test_df
	cleaned_test_df['text'] = cleaned_test_df['text'].map(lambda x: clean_text(x))
	print(cleaned_test_df['text'][0])

# Dummy object to store tweet properties to then write to CSV
class Tweet(object):
	pass

# Make HTTP request to get tweets with keyword, start and end specs
# This function was based on Jefferson-Henrique's `Get Old Tweets Programatically` code
def getTweets(querySearch, st, et, receiveBuffer=None, bufferLength=100, proxy=None):
	refreshCursor = ''
	results = []
	resultsAux = []
	cookieJar = cookielib.CookieJar()
	active = True
	while active:			
		url = "https://twitter.com/i/search/timeline?f=tweets&q=%s&src=typd&max_position=%s" % (urllib.parse.quote(' ' + querySearch + ' since:' + st + ' until:' + et), urllib.parse.quote(refreshCursor))
		headers = [
			('Host', "twitter.com"),
			('User-Agent', "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36"),
			('Accept', "application/json, text/javascript, */*; q=0.01"),
			('Accept-Language', "de,en-US;q=0.7,en;q=0.3"),
			('X-Requested-With', "XMLHttpRequest"),
			('Referer', url),
			('Connection', "keep-alive")
		]
		if proxy:
			opener = urllib.request.build_opener(urllib.ProxyHandler({'http': proxy, 'https': proxy}), urllib.request.HTTPCookieProcessor(cookieJar))
		else:
			opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookieJar))
		opener.addheaders = headers
		try:
			response = opener.open(url)
			jsonResponse = response.read()
		except:
			print("BAD")
			sys.exit()
			return
		myjson = json.loads(jsonResponse)
		if len(myjson['items_html'].strip()) == 0:
			break

		refreshCursor = myjson['min_position']
		scrapedTweets = PyQuery(myjson['items_html'])
		scrapedTweets.remove('div.withheld-tweet')
		tweets = scrapedTweets('div.js-stream-tweet')
		if len(tweets) == 0:
			break
		for tweetHTML in tweets:
			tweetPQ = PyQuery(tweetHTML)
			tweet = Tweet()
			usernameTweet = tweetPQ("span:first.username.u-dir b").text()
			txt = re.sub(r"\s+", " ", tweetPQ("p.js-tweet-text").text().replace('# ', '#').replace('@ ', '@'))
			retweets = int(tweetPQ("span.ProfileTweet-action--retweet span.ProfileTweet-actionCount").attr("data-tweet-stat-count").replace(",", ""))
			favorites = int(tweetPQ("span.ProfileTweet-action--favorite span.ProfileTweet-actionCount").attr("data-tweet-stat-count").replace(",", ""))
			dateSec = int(tweetPQ("small.time span.js-short-timestamp").attr("data-time"))
			id = tweetPQ.attr("data-tweet-id")
			permalink = tweetPQ.attr("data-permalink-path")
			geo = ''
			geoSpan = tweetPQ('span.Tweet-geo')
			if len(geoSpan) > 0:
				geo = geoSpan.attr('title')
			tweet.id = id
			tweet.permalink = 'https://twitter.com' + permalink
			tweet.username = usernameTweet
			tweet.text = txt
			tweet.date = datetime.datetime.fromtimestamp(dateSec)
			tweet.retweets = retweets
			tweet.favorites = favorites
			tweet.mentions = " ".join(re.compile('(@\\w*)').findall(tweet.text))
			tweet.hashtags = " ".join(re.compile('(#\\w*)').findall(tweet.text))
			tweet.geo = geo
			results.append(tweet)
			resultsAux.append(tweet)
			if receiveBuffer and len(resultsAux) >= bufferLength:
				receiveBuffer(resultsAux)
				resultsAux = []
	if receiveBuffer and len(resultsAux) > 0:
		receiveBuffer(resultsAux)
	return results

# File naming convention: vegas_1_500.csv
count = 0

# For each index corresponding to a day, get data and write to appropriate CSV
for i in inds:
	myind = str(i)
	if len(myind) == 1:
		myind = "0" + myind
	filename =queryid+"_"+myind+"_"+"900.csv"
	print(filename)

	outputFileName = filename

	outputFile = codecs.open(outputFileName, "w+", "utf-8")
	outputFile.write('username;date;retweets;favorites;text;geo;mentions;hashtags;id;permalink')

	def receiveBuffer(tweets):
		for t in tweets:
			outputFile.write(('\n%s;%s;%d;%d;"%s";%s;%s;%s;"%s";%s' % (t.username, t.date.strftime("%Y-%m-%d %H:%M"), t.retweets, t.favorites, t.text, t.geo, t.mentions, t.hashtags, t.id, t.permalink)))
		outputFile.flush()
		print('We saved %d tweets:\n' % len(tweets))

	getTweets(query_term, start_time[i], end_time[i], receiveBuffer)


	print("completed request. Now, on to preprocessing.")
	preprocCSV(filename)
	print("done preprocessing :)")
	count += 1
print("done. done. done.")