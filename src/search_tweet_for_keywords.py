from collections import Counter
from urllib.parse import urlparse
import json
import urlexpander
import gzip
import os
import pprint
import pandas as pd
import configparser
import argparse
import sys
import glob

from utils import parse_cl_args,parse_config_file


# This function traverses a dictionary hierarchy (dicts within dicts)
# going through key by key in key_list. If a key is missing it returns
# None. Otherwise, it returns the value of the entry of the final key.
def get_dict_path(d, key_list):
    retval = d
    for k in key_list:
        if k in retval:
            retval = retval[k]
        else:
            return None

    return retval

def get_expanded_urls (twitter_urls_list):
    if twitter_urls_list == None:
        return []
    else:
        return [u['expanded_url'] for u in twitter_urls_list]

def search_tweet_for_keywords (tweet_json, keywords_set):
    """ Takes the json of a tweet and searchs it for terms in the keywords list """

    # Extract text from the four different relevant places it could be
    text = get_dict_path(tweet_json, ['text',])
    extended_text = get_dict_path(tweet_json, ['extended_tweet','full_text'])
    retweeted_text = get_dict_path(tweet_json, ['retweeted_status','text',])
    extended_retweeted_text = get_dict_path(tweet_json, ['retweeted_status','extended_tweet','full_text'])
    quoted_status = get_dict_path(tweet_json, ['quoted_status','text',])
    extended_quoted_status = get_dict_path(tweet_json, ['quoted_status','extended_tweet','full_text',])

    
    
    # Logic to pick out the retweeted text if it exists, and in either case, the extended_tweet
    if retweeted_text:
        if extended_retweeted_text:
            text = extended_retweeted_text
        else:
            text = retweeted_text
    elif extended_text:
        text = extended_text

    if quoted_status:
        if extended_quoted_status:
            text += ' '+ extended_quoted_status
        else:
            text += ' ' + quoted_status
    
            
            
    keywords_found = set()
    if text:
        # If this is a tweet
        
        text += ' ' + ' '.join([u for u in get_expanded_urls(get_dict_path(tweet_json, ['entities','urls']))])
        text += ' ' + ' '.join([u for u in get_expanded_urls(get_dict_path(tweet_json, ['extended_tweet','entities','urls']))])
        text += ' ' + ' '.join([u for u in get_expanded_urls(get_dict_path(tweet_json, ['retweeted_status','entities','urls']))])
        text += ' ' + ' '.join([u for u in get_expanded_urls(get_dict_path(tweet_json, ['retweeted_status','extended_tweet','entities','urls']))])
        text += ' ' + ' '.join([u for u in get_expanded_urls(get_dict_path(tweet_json, ['quoted_status','entities','urls']))])
        text += ' ' + ' '.join([u for u in get_expanded_urls(get_dict_path(tweet_json, ['quoted_status','extended_tweet','entities','urls']))])

        lower_text = text.lower()
        for keyword in keywords_set:
            # All individual words must be present for this keyword to
            # match. We start by assuming the keyword is present.
            keyword_present = True
            for ind_kword in keyword.split(' '):
                if lower_text.find (ind_kword) == -1:
                    # If an individual word isn't present, stop
                    # matching
                    keyword_present = False
                    break
            if keyword_present:
                keywords_found.add(keyword)
            
    #    print (text)
    #    print (keywords_found)
    #    print ('======================')

    return keywords_found
    
def load_keywords_file (path):
    keywords = set()
    for line in open (path):
        keywords.add(line.strip())
    return keywords


def generate_tweet_id_keyword_map (tweet_path, output_path, keywords):
    if os.path.exists(output_path):
        print (output_path,'already exists')
        return -1
        
    output = list()
    counter = 0
    with gzip.open(tweet_path,'r') as f:
        for raw_tweet in f:
            j = json.loads(raw_tweet)
            tid = get_dict_path(j,['id'])
            found_keywords = search_tweet_for_keywords(j,keywords)
            for keyword in found_keywords:
                output += ((tid,keyword),)

            counter += 1

                
    df_out = pd.DataFrame (output,columns=['tweet_id','keyword'])
    df_out.to_csv(output_path, index=False)
    return counter


def generate_tweet_keyword_maps(config, keywords):
    tables_folder = config["PATHS"]["TABLES_DAILY_FOLDER"]
    input_files=glob.glob(config['PATHS']['STREAMING_FILES_FOLDER']+'/*gz')

    num_tweets_processed = 0
    for in_file in input_files:
        day = in_file.replace(config["PATHS"]["STREAMING_FILES_FOLDER"] + "/streaming_data--", "").replace(".json.gz", "")  
        output_file = os.path.join(config["PATHS"]["TABLES_DAILY_FOLDER"], str(day) + "_tweet_keywords_full_table.csv")
        if os.path.exists (output_file):
            print ("Already processed", output_file)
        else:
            num_tweets_processed += generate_tweet_id_keyword_map(in_file, output_file, keywords)
            print ('Processed',num_tweets_processed,'for',day)
        
    
if __name__ == '__main__':
    config_file_path = parse_cl_args()
    config = parse_config_file(config_file_path)

    keywords = load_keywords_file ('keywords.txt')

    generate_tweet_keyword_maps(config,keywords)

    sys.exit(0)
        
