# Scripts

1. `get_cases_and_deaths.py` - download usa-facts [cases and deaths data](https://cmu-delphi.github.io/delphi-epidata/api/covidcast-signals/usa-facts.html) using [CMU CovidCast API](https://cmu-delphi.github.io/delphi-epidata/api/covidcast.html)
2. `aggregate_cases_and_deaths.py` - aggregate the data that was downloaded with `get_cases_and_deaths.py`
3. `utils.py` - a collection of convenience functions used in other scripts
4. `build_fips_data_table.py` - a script which cleans `data/misc/all-geocodes-v2018-RAW.csv` and creates a new file `fip_code_lookup.csv` that is used in the utils.Geo() class
5. `merge_datasets.py` - a script for merging the different data sets to create a single master data file saved in `data/master_merged`
6. `twitter_data_processing.py` - a script for processing Twitter data and produce intermediate  tables (|tweet_id|variable|) that are merged together to produce statistics on misinformation at account-level.
7. `search_tweet_for_keywords.py` - a script to match tweets against a set of keywords
> **Note:** See the above files for details on their purpose, inputs, outputs, etc.


