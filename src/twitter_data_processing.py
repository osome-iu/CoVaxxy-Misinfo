import json
import gzip
from carmen import get_resolver
from carmen.location import Location
from collections import defaultdict
import timeit
import csv
from utils import parse_cl_args, parse_config_file
from search_tweet_for_keywords import load_keywords_file, search_tweet_for_keywords
import pandas as pd
import sys
import tldextract
import requests
import concurrent.futures
import queue
import glob
import os
import pickle as pkl
import urlexpander

DEFAULT_START_DATE = "2021-01-04"
DEFAULT_END_DATE = "2021-03-25"
KEYWORDS = ["vaccine", "vaccination", "vaccinate", "vax"]


def get_urls(urls_entry):
    urls = set()
    for u in urls_entry:
        url = u['url']
        if 'expanded_url' in u:
            url = u['expanded_url']
        urls.add(url)
    return (urls)


def get_dict_path(d, key_list):
    retval = d
    for k in key_list:
        if k in retval:
            retval = retval[k]
        else:
            return None
    return retval


def extract_top_domain(url):
    """ Function to extract top level domain of an URL """
    tsd, td, tsu = tldextract.extract(url)
    domain = td + '.' + tsu
    return domain.lower()


HTTP_TIMEOUT = 20

def infer_base_url(domain):
    """Fetch the base URL of a domain by sending HTTP HEAD request."""
    try:
        r = requests.head(
            domain,
            allow_redirects=True,
            timeout=HTTP_TIMEOUT)
        base_url = r.url
        if not base_url.endswith('/'):
            base_url = base_url + '/'
    except Exception as e:
        print(e)
        base_url = domain
    return base_url


def expand_urls(config):

    short_link_services = [
        'bit.ly',
        'dlvr.it',
        'liicr.nl',
        'tinyurl.com',
        'goo.gl',
        'ift.tt',
        'ow.ly',
        'fxn.ws',
        'buff.ly',
        'back.ly',
        'amzn.to',
        'nyti.ms',
        'nyp.st',
        'dailysign.al',
        'j.mp',
        'wapo.st',
        'reut.rs',
        'drudge.tw',
        'shar.es',
        'sumo.ly',
        'rebrand.ly',
        'covfefe.bz',
        'trib.al',
        'yhoo.it',
        't.co',
        'shr.lc',
        'po.st',
        'dld.bz',
        'bitly.com',
        'crfrm.us',
        'flip.it',
        'mf.tt',
        'wp.me',
        'voat.co',
        'zurl.co',
        'fw.to',
        'mol.im',
        'read.bi',
        'disq.us',
        'tmsnrt.rs',
        'usat.ly',
        'aje.io',
        'sc.mp',
        'gop.cm',
        'crwd.fr',
        'zpr.io',
        'scq.io',
        'trib.in',
        'owl.li',
        'youtu.be',
    ]

    urls_table = pd.read_csv(os.path.join(config["PATHS"]["INTERMEDIATE_DATA_DIR"], "tweet_url_table.csv"),
                             usecols=["tweet_id", "url"])

    urls_tweet_id = dict()
    for ix, row in urls_table.iterrows():
        url = row["url"]
        tweet_id = row["tweet_id"]
        domain = extract_top_domain(url)
        if domain in short_link_services:
            urls_tweet_id[url] = tweet_id

    print("No. urls to expand: " + str(urls_tweet_id.__len__()))

    q = queue.Queue()

    def expand_domain(short_url):
        expanded_url = infer_base_url(short_url)
        top_domain = extract_top_domain(expanded_url)
        q.put([short_url, expanded_url, top_domain])
        print("Working on {}, {} ".format(short_url, len(q.queue)))

    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        executor.map(expand_domain, list(urls_tweet_id.keys()))

    res_df = pd.DataFrame(list(q.queue), columns=['short_url', 'expanded_url', 'top_domain'])

    print("Updating links")
    expanded_urls_dict = dict()
    for ix, row in res_df.iterrows():
        old = row["short_url"]
        new = row["expanded_url"]
        if old == new:  # it wasn't expanded: lets try with urlexpander
            try:
                new_v2 = urlexpander.expand(old)
                if new_v2:
                    new = new_v2
            except:
                pass
        expanded_urls_dict[old] = new
    pkl.dump(expanded_urls_dict,
             open(os.path.join(config["PATHS"]["INTERMEDIATE_DATA_DIR"], "urls_expanded.pkl"), "wb"))


## Function to build tables to associate tweets with URLs, keywords, accounts and locations
def build_tables(config):
    """
    Function to associate tweets with URLs, keywords, accounts and locations.
    Parameters:
        config (dict): A dictionary with config information about paths and filenames
    Output:
        It saves several dataframes with two columns depending on the object associated:
        1) | tweet_id | account_id |
        2) |tweet_id | location |
        ... etc
    """

    ## Initialize carmen geolocation

    resolver = get_resolver()
    resolver.load_locations()

    ## dictionaries for the association tweet -> object
    tweet_account = defaultdict()
    tweet_location = defaultdict()
    tweet_carmen_location = defaultdict()
    tweet_url = defaultdict(list)
    tweet_keyword = defaultdict(list)

    ## load file of keywords
    keywords = load_keywords_file('keywords.txt')

    for file in sorted(glob.glob(
            config["PATHS"]["TW_FILES_FOLDER"] + "/*json")):  # iterating over all Twitter data files
        print("Processing : " + str(file))
        start = timeit.default_timer()  # to monitor running time
        tweet_url = defaultdict(list)
        with open(file, 'r') as f:
            for line in f.readlines():
                try:
                    j = json.loads(line)
                    tweet_id = j["id_str"]

                    ## 1) extracting all URLs from tweets/retweets (including extended) ##
                    found_urls = set()
                    urls_entry = get_dict_path(j, ['entities', 'urls'])
                    if urls_entry:
                        found_urls = found_urls.union(get_urls(urls_entry))
                    urls_entry = get_dict_path(j, ['extended_tweet', 'entities', 'urls'])
                    if urls_entry:
                        found_urls = found_urls.union(get_urls(urls_entry))
                    urls_entry = get_dict_path(j, ['retweeted_status', 'entities', 'urls'])
                    if urls_entry:
                        found_urls = found_urls.union(get_urls(urls_entry))
                    urls_entry = get_dict_path(j, ['retweeted_status', 'extended_tweet', 'entities', 'urls'])
                    if urls_entry:
                        found_urls = found_urls.union(get_urls(urls_entry))

                    for url in found_urls:  # iterate over the SET of found URLs
                        domain = extract_top_domain(url)
                        if domain == "twitter.com":  # ignore twitter.com
                            continue
                        # associate tweet_id and url
                        tweet_url[tweet_id].append(url)

                    ## 2) extracting account, its location and matching it with carmen ##
                    account = j["user"]
                    account_id = j["user"]["id_str"]

                    tweet_account[tweet_id] = account_id

                    tweet_location[tweet_id] = str(account["location"])

                    result = resolver.resolve_tweet({'user': account})
                    if not result:
                        match = "No match!"
                    else:
                        match = str(result[1])
                        # result[1] is a Location() object, e.g. Location(country='United Kingdom', state='England', county='London', city='London', known=True, id=2206)

                    tweet_carmen_location[tweet_id] = match

                    ## 3) match keywords in the tweet ##
                    found_keywords = search_tweet_for_keywords(j, keywords)
                    for keyword in found_keywords:
                        tweet_keyword[tweet_id].append(keyword)

                except Exception as e:
                    print(e)
                    print(line)
    print("Processed tweets: " + str(tweet_account.__len__()))

    i = 0
    ## Manually writing tables to .csv files ##
    names = ["account", "location", "carmen_location", "url", "keyword"]
    for data in [tweet_account, tweet_location, tweet_carmen_location, tweet_url,
                 tweet_keyword]:  # looping over different dictionaries
        name = names[i]
        print("Dumping table for "+str(name))
        i += 1  # increment to get to other names

        filepath = os.path.join(config["PATHS"]["INTERMEDIATE_DATA_DIR"], "tweet_" + name + "_table.csv")
        with open(filepath, 'w', newline='') as csvfile:
            fieldnames = ['tweet_id', name]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',')
            writer.writeheader()
            for k in data:
                if name in ["url", "keyword"]: # the mapping is tweet_id -> list(objects), need a different way to write this
                    for val in data[k]:
                        writer.writerow({'tweet_id': k, name: val}) 
                else:
                    writer.writerow({'tweet_id': k, name: data[k]})


def merge_tables(config):
    """
    Function to merge all intermediate tables (i.e. url, account, location, carmen_location, keyword). It also takes into account
    expanded URLs before merging the tables.
    Parameters:
        config (dict): A dictionary with config information about paths and filenames. It is used also to get the Iffy+ list of low-cred websites
    Output:
        It saves a dataframe with several columns:
        - "tweet_id", the id of the tweet
        - "url", the URL shared (if present, else NA)
        - "expanded", the expanded version of the URL if it was shortened; it is equal to "url" if it was not expanded (if present, else NA)
        - "domain", the domain of the URL shared (if present, else NA)
        - "account_id", the id of Twitter user who shared the tweet;
        - "location", the "location" field of Twitter user objects (it can be "None")
        - "carmen_location", the result of using "carmen" API on each location (converted to string) = Location() if matches something, else "No match!"
        - "low_cred_flag", a boolean flag indicating whether the "domain" shared belongs to the low-credibility list
        - "keyword", the keyword matching that tweet (from the "keywords.txt" list of terms used in Covaxxy)
    """
    low_cred_df = pd.read_csv(os.path.join(config["PATHS"]["INTERMEDIATE_DATA_DIR"], config["FILES"]["LOW_CRED_FILE"]))
    low_cred_sources = set(low_cred_df["site"].values)

    start = timeit.default_timer()

    tweet_url = pd.read_csv(os.path.join(config["PATHS"]["INTERMEDIATE_DATA_DIR"], "tweet_url_table.csv"))
    try:
        tweet_url_expanded_dict = pkl.load(
            open(os.path.join(config["PATHS"]["INTERMEDIATE_DATA_DIR"], "urls_expanded.pkl"), "rb"))
    except:
        tweet_url_expanded_dict = {}
        print(
            "You didn't expand URLs. Press CTRL+C to interrupt and run the expanding script if you don't want to miss relevant URLs.")
    expanded_urls = []
    domains = []
    for ix, row in tweet_url.iterrows():  # taking into account expanded version of certain urls
        url = row["url"]
        if url in tweet_url_expanded_dict:
            expanded = tweet_url_expanded_dict[url]
        else:
            expanded = url
        expanded_urls.append(expanded)
        domain = extract_top_domain(expanded)
        domains.append(domain)

    tweet_url["expanded"] = expanded_urls
    tweet_url["domain"] = domains

    tweet_account = pd.read_csv(os.path.join(config["PATHS"]["INTERMEDIATE_DATA_DIR"], "tweet_account_table.csv"))

    tweet_location = pd.read_csv(os.path.join(config["PATHS"]["INTERMEDIATE_DATA_DIR"], "tweet_location_table.csv"))

    tweet_carmen_location = pd.read_csv(
        os.path.join(config["PATHS"]["INTERMEDIATE_DATA_DIR"], "tweet_carmen_location_table.csv"))

    tweet_keyword = pd.read_csv(os.path.join(config["PATHS"]["INTERMEDIATE_DATA_DIR"], "tweet_keyword_table.csv"))

    ## merging everything, how="left" is to retain tweets without URLs nor keywords
    data = tweet_account.merge(tweet_location, on="tweet_id").merge(
        tweet_carmen_location, on="tweet_id").merge(tweet_keyword, on="tweet_id", how="left").merge(tweet_url,
                                                                                                    on="tweet_id",
                                                                                                    how="left")
    ## checking which tweets contain low-credibility
    data["low_cred_flag"] = data.domain.apply(lambda x: x in low_cred_sources)

    ## writing dataframe using csv file because it's safer
    with open(os.path.join(config["PATHS"]["INTERMEDIATE_DATA_DIR"], "tweet_merged_table.csv"), 'w',
              newline='') as csvfile:
        fieldnames = data.columns
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',')
        writer.writeheader()
        for ix, row in data.iterrows():
            writer.writerow({k: row[k] for k in row.index})

    end = timeit.default_timer()
    print("Running time: " + str(end - start) + " seconds")


def get_US_accounts_table(config, kw_filter=False, keywords=KEYWORDS):
    """
    Function to extract final table with statistics for US-based accounts, also filtering for tweets which match certain keywords.

    """

    df = pd.read_csv(os.path.join(config["PATHS"]["INTERMEDIATE_DATA_DIR"],
                                  "tweet_merged_table.csv"))
    if kw_filter:
        df = df[df["keyword"].isin(keywords)]

    us_data = df[df["carmen_location"].str.contains("United States")]  # filtering for US accounts

    # Computing stats for US accounts
    acc_stats = dict()
    for ix, data in us_data.groupby("account"):
        location = eval(str(data.carmen_location.values[0]))

        no_tweets = data["tweet_id"].nunique()
        try:
            no_low_cred_tweets = data["low_cred_flag"].value_counts()[True]
        except:
            no_low_cred_tweets = 0

        acc_stats[ix] = {'no_tweets': no_tweets, 'no_low_cred_tweets': no_low_cred_tweets,
                         'state': str(location.state), 'county': str(location.county)}

    df = pd.DataFrame.from_dict(acc_stats, orient="index")
    df = df.reset_index()
    df = df.rename(columns={'index': 'account_id'})

    ## now group by account and sum stats
    acc_stats = dict()
    for ix, data in df.groupby("account_id"):
        no_tweets = data["no_tweets"].sum()
        no_low_cred_tweets = data["no_low_cred_tweets"].sum()
        fraction_misinfo = (no_low_cred_tweets / no_tweets) * 100
        acc_stats[ix] = {'state': data['state'].values[0], 'county': data['county'].values[0],
                         'no_tweets': no_tweets, 'no_low_cred_tweets': no_low_cred_tweets,
                         'fraction_misinfo': fraction_misinfo}

    final_df = pd.DataFrame.from_dict(acc_stats, orient="index")
    final_df = final_df.reset_index()
    final_df = final_df.rename(columns={'index': 'account_id'})

    kw = "_keywords_filtered_" if kw_filter else ""

    final_df.to_csv(os.path.join(config["PATHS"]["INTERMEDIATE_DATA_DIR"],
                                 "US_accounts_" + kw + "table.csv"), index=False)


if __name__ == "__main__":
    try:
        cwd = os.getcwd()

        if os.path.basename(cwd) != "src":
            raise Exception("CHANGE CURRENT WORKING DIRECTORY TO THE `src` PATH BEFORE RUNNING!!")
        
        args = parse_cl_args()
        config_file_path = args.config_file
        
        # Parse config file
        config = parse_config_file(config_file_path)
        
        kw_filter = args.keywords_filter

        print("Building tables.")
        build_tables(config)
        print("Expanding URLs.")
        expand_urls(config)
        print("Merging tables.")
        merge_tables(config)
        print("Getting US accounts table.")
        get_US_accounts_table(config, kw_filter)

        exit(0)
    except Exception as e:
        print(e)
        exit(1)
