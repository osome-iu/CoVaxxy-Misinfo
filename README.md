Reproducibility code for "The impact of online misinformation on U.S. COVID-19 vaccinations" Francesco Pierri, Brea Perry, Matthew R. DeVerna, Kai-Cheng Yang, Alessandro Flammini, Filippo Menczer and John Bryden.

## Structure
      .
      ├── README.md 
      ├── config.ini 
      └── data
      │   ├── county_level
      │   ├── covid19
      │   ├── misc
      │   ├── state_level
      │   └── twitter
      ├── intermediate_files
      ├── logs
      ├── output_files
      └── src

* `config.ini` - configuration file that specifies paths and filenames for the scripts
* `data` - folder which contains subfolders with raw data at the state and county level, as well as Twitter data. Check related README files for further details
* `intermediate_files` - folder which contains intermediate data to be merged
* `logs` - folder which contains logs for the output of scripts
* `src` - folder which contains scripts to be executed

## Keywords and Low-credibility sources
You can find keywords used to filter Twitter stream in `src/keywords.txt`. You can find the list of low-credibility sources in `intermediate_files/low_credibility.csv`. Check the [Github repository](https://github.com/osome-iu/CoVaxxy) associated to our CoVaxxy project for further details.

## Instructions to replicate results

1. Put Twitter data in the `data/twitter` folder. You must put `.json` files with one tweet `json` per line. Check the [Github repository](https://github.com/osome-iu/CoVaxxy) associated to our CoVaxxy project to see how to download our dataset and reconstruct it using Twitter API.
2. Move in the `src` folder and execute Python scripts (see associated `src/README.md` file for further details) in the following order:
      * `python3 twitter_data_processing.py ../config.ini` - to process Twitter data
      * `python3 get_cases_and_deaths.py ../config.ini` - download COVID-19 number of cases and deaths; modify `config.ini` to set the date range.
      * `python3 aggregate_cases_and_deaths.py ../config.ini` - aggregate COVID-19 numbers of cases and deaths for further use
      * `python3 merge_datasets.py ../config.ini` - merge together intermediate data in a single dataframe to be used for correlation
3. Run STATA script (`src/stata_script.do`) to get correlation results

## Dependencies
* `covidcast` - install by running the below code from your terminal
    * `pip install covidcast`
    * Details can be found [here](https://cmu-delphi.github.io/delphi-epidata/api/covidcast.html)
* `carmen`  - install by running the below code from your terminal
    * `pip install carmen`
    * Details can be found [here](https://github.com/mdredze/carmen-python)
