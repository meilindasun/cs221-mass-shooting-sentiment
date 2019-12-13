# cs221-mass-shooting-sentiment
Stanford CS 221 final project -- Measuring apathy toward mass shootings through Twitter sentiment analysis

``getTweetDataCSV.py`` scrapes tweets from Twitter filtering by keyword (in our case the location of a given shooting) and accepting start and end timestamp parameters. Our logic interpreteing json responses received from the web in getTweets is based on Jefferson-Henrique's GetOldTweets project (https://github.com/Jefferson-Henrique/GetOldTweets-python). Tweets randomly sampled from each day tested are written to a CSV file named in the following format: [shooting name]\_[num days since first sampled]\_[num tweets collected].csv e.g. ``vegas_1_300.csv`` if we have written 300 tweets about the Las Vegas shooting sampled from the first day we examine.
