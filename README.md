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
* `data` - folder which contains subfolders with raw data at the state and county level, as well as Twitter data
* `intermediate_files` - folder which contains intermediate data to be merged
* `logs` - folder which contains logs for the output of scripts
* `src` - folder which contains scripts to be executed
    
## Dependencies
* `covidcast` - install by running the below code from your terminal
    * `pip install covidcast`
    * Details can be found [here](https://cmu-delphi.github.io/delphi-epidata/api/covidcast.html)
* `carmen`  - install by running the below code from your terminal
    * `pip install carmen`
    * Details can be found [here](https://github.com/mdredze/carmen-python)

## Instructions to replicate results

1. Put Twitter data in the `data/twitter` folder. You must put one or several files with one `json` (i.e. one tweet) per line. Check the [Github repository](https://github.com/osome-iu/CoVaxxy) associated to our CoVaxxy project to see how to download our dataset and reconstruct it using Twitter API.
2. Execute scripts in the `src` folder (see associated `src/README.md` file for further details)
3. TODO (correlation)
