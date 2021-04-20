"""
PURPOSE:
    - This package contains a number of convenience functions
    which are used in scripts throughout this project's data
    analysis.

"""
import argparse
import configparser
import datetime
import logging
import os

import pandas as pd

class Geo:
    """A convenience class for geographic codes."""

    def __init__(self):
        state_abbrv_to_full_path = "../data/misc/abbr-name.csv"
        fip_code_lookup_path = "../data/misc/fip_code_lookup.csv"

        self._state_abbrv_lookup = pd.read_csv(
            state_abbrv_to_full_path,
            names = ["Abbr", "State"],
            dtype = {
                "Abbr":str,
                "State":str
            }
        )
        self._fip_code_lookup = pd.read_csv(
            fip_code_lookup_path,
            dtype={
                'geo_level':str,
                'state_code_fips':str,
                'county_code_fips':str,
                'area_name':str,
                'fips_code':str
            }
        )

    def load_state_abbrv_lookup(self, as_dict=False):
        """Return state abbrv. to full name lookup table.
            - Pass `as_dict = True` to get a dictionary
        """

        if as_dict:
            state_lookup = self._state_abbrv_lookup
            zipper = zip(state_lookup["Abbr"], state_lookup["State"])
            sl_dict = {abbr:state for abbr,state in zipper}

            return sl_dict

        return self._state_abbrv_lookup

    def load_fip_code_lookup(self):
        """Return fip code lookup table."""
        return self._fip_code_lookup

    def get_county_state_to_fips_map(self, unique_fips=True):
        fips=self._fip_code_lookup

        states = fips[fips.geo_level == 'State'].copy()[['state_code_fips','area_name']]
        states=states.rename(columns={'area_name':'State'})

        counties = fips[fips.geo_level == 'County'].copy()[['state_code_fips','area_name','fips_code']]
        counties= counties.rename(columns={'area_name':'County'})

        county_fips_map = pd.merge(states,counties,on='state_code_fips')

        if unique_fips:
            county_fips_map = county_fips_map.drop_duplicates(subset=['fips_code'])
        
        return county_fips_map

    def get_state_to_fips_map(self, unique_fips=True):
        fips=self._fip_code_lookup

        states = fips[fips.geo_level == 'State'].copy()[['area_name','fips_code']]
        states=states.rename(columns={'area_name':'State','fips_code':'FIPS'})

        state_abbr = self._state_abbrv_lookup.copy()
        state_abbr['abbr_lower'] = state_abbr.Abbr.apply(lambda x:x.lower())
        states = pd.merge(states,state_abbr,on='State')
        
        return states.reset_index()


    
def get_logger(LOG_DIR, LOG_FILE):
    """Create logger."""

    # Create LOG_DIR if it doesn't exist already
    if not os.path.exists(LOG_DIR):
        os.makedirs(f"{LOG_DIR}")

    try:
        # Create logger and set level
        logger = logging.getLogger(__name__)
        logger.setLevel(level=logging.INFO)

        # Configure file handler
        formatter = logging.Formatter(
            fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt = "%Y-%m-%d_%H-%M-%S"
            )
        fh = logging.FileHandler(f"{os.path.join(LOG_DIR,LOG_FILE)}")
        fh.setFormatter(formatter)
        fh.setLevel(level=logging.INFO)

        # Add handlers to logger
        logger.addHandler(fh)
        return  logger

    except Exception as e:
        print("Problem getting logger.")
        print(e)

def parse_cl_args():
    """Set CLI Arguments."""

    try:
        # Initialize parser
        parser = argparse.ArgumentParser()
        # Add optional arguments
        parser.add_argument(
            "-c", "--config-file",
            metavar='Config-file',
            help="Full path to the config file containing paths/file names for script.",
            required=True
        )
        parser.add_argument(
            "-s", "--state_level",
            help="Calculate at the state level",
            action='store_true'
        )
        parser.add_argument(
            "-k", "--keywords_filter",
            help="Use keywords filter",
            action='store_true'
        )
            
        # Read parsed arguments from the command line into "args"
        args = parser.parse_args()

        # Assign the file name to a variable and return it
        return args

    except Exception as e:
        print("Problem parsing command line input.")
        print(e)

def parse_config_file(config_file_path):
    """Parse config file from provided path"""

    try:
        config = configparser.ConfigParser()
        config.read(config_file_path)
        return config

    except Exception as e:
        print("Problem parsing config file.")
        print(e)

def convert_date_str_to_datetime(date):
    """Convert input string date to datetime object format"""

    print(f"\t| Converting input date - {date} - to datetime object...")
    try:

        # Convert string date (YYYY-MM-DD) to datetime w/ timezone
        date = datetime.datetime.strptime(date,"%Y-%m-%d")

        print("\t| ~~Success~~")
        return date

    except Exception as e:
        print("Problem converting date to datetime object.")
        print(e)
