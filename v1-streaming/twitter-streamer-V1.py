#!/usr/bin/env python3

"""
PURPOSE: 
    - To create a real-time FILTERED stream of Twitter
    data, utilizing the Twitter V1 API.

INPUT:
    - A file with keywords/hashtags (one per line) that
    will be utilized as the filters matching to tweets 
    in real-time.

OUTPUT:
    - One JSON file is created - per day - where each
    line item represents one tweet object. 

DEPENDENCIES:
    - Tweepy (https://www.tweepy.org/)

Author: Matthew R. DeVerna
"""

# Import packages
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

import argparse
import configparser
import json
import logging
import os
import sys
import time
from datetime import datetime as dt

# Dependencies
from tweepy import OAuthHandler, Stream, StreamListener



# Build Functions.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Listener(StreamListener):
    """ 
    The Listener wraps tweepys StreamListener allowing customizable handling
    of tweets and errors received from the stream.

    This Listener does the following:
        - Writes raw tweet data to a file named for the day it is scraped.
    """

    def __init__(self,logger_):
        self.logger = logger
        self.output_file= None
        self.output_day = ""
    
    def get_output_file(self,today):
        if self.output_day != today or self.output_file is None:
            data_filename = f"streaming_data--{today}.json"
            full_file_path = os.path.join(PATHS["data_dir"], data_filename)
            """
            The 'if os.path.isfile():' line below checks if the data 
            file has already been created for a given day. In effect,
            this creates a new file for each day as the date is checked
            each time data is downloaded from Twitter.

            """
            if os.path.isfile(full_file_path):
                self.output_file = open(full_file_path, "a+", buffering = 65536)

            else:
                logger.info(f"Creating file: {full_file_path}")
                self.output_file = open(full_file_path, "a+", buffering = 65536)
                
            self.output_day = today
            
        return self.output_file
            
    
    def on_data(self, data):
        """Do this when we get data."""

        today = dt.strftime(dt.now(), "%Y-%m-%d")
        #        print (data)
        try:
            f = self.get_output_file(today)
            f.write(f"{data}")
        except Exception as e:
            logger.error("Error: "+str(e), exc_info=True)


        return True


    def on_error(self, status_code):
        """Do this if we get an error."""

        # Log error with exception info
        logger.error(f"Error, code {status_code}", exc_info=True)
        if status_code == 420:
            # Rate limit hit

            # Wait five minutes
            logger.info("Rate limit reached. Sleeping for five minutes.")
            time.sleep(300)
            return True

        elif status_code == 503:
            # Twitter Service Unavailable

            # Wait 60 seconds and retry
            # Connection retry limits are 5 connection attempts per 5 min
                # https://developer.twitter.com/en/docs/twitter-api/tweets/filtered-stream/migrate
            logger.info("Twitter service unavailable. Sleeping for one minute.")
            time.sleep(60)
            return True

        else:
            return True


def parse_cl_args():
    """Parse command line arguments."""

    # Initiate the parser w. a simple description.
    parser = argparse.ArgumentParser(
      description="Scrape real-time tweets from Twitter using the V1 API based on keywords passed via file."
      )
    # Add optional arguments
    parser.add_argument(
      "-cf", "--config-file", 
      metavar='Config File',
      help="Full path to your configuration file (config.ini)."
      )

    # Read parsed arguments from the command line into "args"
    args = parser.parse_args()

    # Assign them to objects
    config_file = args.config_file

    return config_file


def load_config(config_file):
    """Load details from configuration file."""

    # Initialize config parser
    config = configparser.ConfigParser()

    # Read in parameters
    config.read(config_file)

    # Split TWITTER_CREDS and PATHS
    TWITTER_CREDS = config['TWITTER_CREDS']
    PATHS = config['PATHS']

    return TWITTER_CREDS, PATHS


def load_terms(file,logger):
    """Load keywords file."""
    logger.info("Attempting to load filter rules...")

    filter_terms = []
    with open(file, "r") as f:
        for line in f:
            logger.info("Loaded Filter Rule: {}".format(line.strip('\n')))
            filter_terms.append(line.strip("\n"))

    logger.info("[*] Filter rules loaded succesfully.")
    return filter_terms


def get_logger(log_dir, full_log_path):
    """Create logger."""

    # Create log_dir if it doesn't exist already
    try:
        os.makedirs(f"{log_dir}")
    except:
        pass

    # Create logger and set level
    logger = logging.getLogger(__name__)
    logger.setLevel(level=logging.INFO)

    # Configure file handler
    formatter = logging.Formatter(
        fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt = "%Y-%m-%d_%H-%M-%S")
    fh = logging.FileHandler(f"{full_log_path}")
    fh.setFormatter(formatter)
    fh.setLevel(level=logging.INFO)

    # Add handlers to logger
    logger.addHandler(fh)

    return  logger



# Execute main program.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if __name__ == '__main__':
    # Get current time
    start_time = dt.strftime(dt.now(), '%Y-%m-%d_%H-%M-%S')

    # Parse command line arguments
    #   This simple returns the path to the configuration file
    config_file = parse_cl_args()

    # Load configuration parameters
    TWITTER_CREDS, PATHS = load_config(config_file)

    # Define full path to log file name and create logger named 'log'
    full_log_path = os.path.join(PATHS["log_dir"], f"{start_time}_stream.log")
    logger = get_logger(
        log_dir = PATHS["log_dir"], 
        full_log_path= full_log_path
        )

    # Log start time and
    logger.info(f"Script started {start_time}")
    logger.info(f"Following config parameters passed:")
    logger.info(f"[*] KEYWORDS_FILE  : {PATHS['keywords_file']}")
    logger.info(f"[*] DATA_DIRECTORY : {PATHS['data_dir']}")
    logger.info(f"[*] LOG_DIRECTORY  : {PATHS['log_dir']}")

    # Create data dir if it doesn't exist already
    try:
        os.makedirs(f"{PATHS['data_dir']}")
    except:
        pass
    
    # Load file terms...
    filter_terms = load_terms(PATHS["keywords_file"],logger)

    # Set up the stream.
    logger.info("Intializing the stream...")
    listener = Listener(logger)
    auth = OAuthHandler(TWITTER_CREDS["api_key"], TWITTER_CREDS["api_key_secret"])
    auth.set_access_token(TWITTER_CREDS["access_token"], TWITTER_CREDS["access_token_secret"])
    stream = Stream(auth, listener)
    logger.info("[*] Stream initialized succesfully.")

    # Begin the stream.
    logger.info("[*] Beginning stream...")
    while True:
        try:
            stream.filter(track=filter_terms, languages=["en"])
        except KeyboardInterrupt:
            logger.info("User manually ended stream with a Keyboard Interruption.")
            sys.exit("\n\nUser manually ended stream with a Keyboard Interruption.\n\n")
        except Exception as e:
            logger.debug('Unexpected exception: %s %e')
            continue
