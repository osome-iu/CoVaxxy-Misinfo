import pandas as pd
import json
import sys
import glob as glob
import gzip
import os
import configparser
import tldextract
from carmen import get_resolver
from carmen.location import Location
from collections import defaultdict
import timeit
import pickle as pkl
import csv
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from utils import parse_cl_args, parse_config_file, Geo

# Load config_file_path from commandline input
args = parse_cl_args()
config_file = args.config_file

config = configparser.ConfigParser()
# Read in parameters
config.read(config_file)

## Read daily files
dates = pd.date_range("2021-01-04", "2021-03-25")
dfs = []
for day in dates:
    day_string = day.strftime("%Y-%m-%d")
    df = pd.read_csv(os.path.join(config["PATHS"]["TABLES_DAILY_FOLDER"],
                           str(day_string) + "_US_accounts_table.csv"))
    df["day"] = [day for i in range(df.__len__())]
    dfs.append(df)
dfs = pd.concat(dfs) # concatenating all daily results

## Produce N-day results
N = '1'
if not os.path.exists(os.path.join(config["PATHS"]["TABLES_TEMPORAL_FOLDER"], N+"day")):
  os.makedirs(os.path.join(config["PATHS"]["TABLES_TEMPORAL_FOLDER"], N+"day"))
 
## Resample dates and produce aggregated data
for ix, df in dfs.resample(N+'D', on ="day"):
    start_date = min(df["day"]).strftime("%Y-%m-%d")
    end_date = max(df["day"]).strftime("%Y-%m-%d")
    print(start_date + " to " + end_date)
    ## now group by account and sum stats
    final_df = df.groupby(["account_id", "state", "county"]).sum().reset_index()
    final_df = final_df.reset_index()
    final_df["fraction_misinfo"] = (final_df["no_low_cred_tweets"]/final_df["no_tweets"])

    
    final_df.to_csv(os.path.join(config["PATHS"]["TABLES_TEMPORAL_FOLDER"],
                                        N+"day/"+start_date+"_"+end_date+"_US_accounts_aggregated_table.csv"), index=False)

    
