# v1 Twitter Streamer

This is a tweet streaming pipeline that can be set up to stream tweets from Twitter by following the [below steps](#setting-up-the-pipeline).

* [Setting up the Pipeline](#setting-up-the-pipeline)
    * [How to download tweets with `twitter-streamer-V1.py`](#how-to-download-tweets-with-twitter-streamer-v1py)
* [Using `supervisor` with `twitter-streamer-V1.py`](#using-supervisor-with-twitter-streamer-v1py)
    * [Killing `supervisor`](#killing-supervisor) 
    * [`supervisor` logs/files](#supervisor-logsfiles)
* [Details on Collected Tweets](#details-on-collected-tweets)

## Setting Up the Pipeline

This pipeline utilizes Python 3 so this needs to be installed before doing anything else. 
* [https://www.python.org/download/releases/3.0/](https://www.python.org/download/releases/3.0/)

**Follow these steps to get the stream started.**
1. `ssh` into your JetStream virtual machine's home directory as usual.
2. Clone the `vaccines/streaming-branch` repo into your home directory by entering the below:
    * `git clone --single-branch --branch stream-framework https://github.iu.edu/NaN-team/vaccines.git` 
    * This will download the necessary files to your home directory. If you type `ls` and then hit `ENTER` you should see the new files within a folder called `vaccines`.
3. Enter the `v1-streaming` directory and edit the `config.ini` by entering the below into the command line
    * `nano ./vaccines/v1-streaming/config.ini`, then
        * This command will open your `nano` editor to edit the file and you should see the below.
    ```shell
    # Your Twitter credentials
    [TWITTER_CREDS]
    access_token = INSERT_TOKEN_HERE
    access_token_secret = INSERT_TOKEN_HERE
    api_key = INSERT_KEY_HERE
    api_key_secret = INSERT_KEY_HERE

    # Important paths:
    #   - keywords_file = the path to a file with keywords to match within your streamer
    #   - data_dir = where tweets will be saved
    #   - log_dir = where your log file will be saved
    [PATHS]
    keywords_file = /home/**YOUR_USERNAME**/vaccines/v1-streaming/keywords.txt
    data_dir = /**YOUR_DATA_VOLUME**/stream/tweet_data/
    log_dir = /**YOUR_DATA_VOLUME**/stream/logs/
    ```
4. Paste in your twitter credentials in the proper location.
5. Substitute `**YOUR_USERNAME**` with your own username for the `keywords_file` line (find this out by entering `whoami` from the terminal) 
6. Substitute `**YOUR_DATA_VOLUME**` with the name of your virtual machine's data volume. This will be the location on your virtual machine where you intend to store all of your data.
7. Save this file and exit `nano`.
8. Enter the below into your command line:
    * `pip3 install tweepy`
    * This will install the `tweepy` package if it is not already installed.
    * Either way, to check if this package is installed, you can type `pip show tweepy` which should then display something like the below

    ```shell
    Name: tweepy
    Version: 3.8.0
    Summary: Twitter library for python
    Home-page: http://github.com/tweepy/tweepy
    Author: Joshua Roesslein
    Author-email: tweepy@googlegroups.com
    License: MIT
    Location: /Users/matthewdeverna/anaconda3/lib/python3.7/site-packages
    Requires: six, PySocks, requests, requests-oauthlib
    ```

### How to download tweets with `twitter-streamer-V1.py`
At this point your python script is ready to go and can be utilized by calling the function in the following way:
* `python3 twitter-streamer-V1.py -cf path/to/config.ini`
> Note: python3 twitter-streamer-V1.py -h for help

### Using `supervisor` with `twitter-streamer-V1.py`
You will notice a folder `/vaccines/v1-streaming/supervisor` which contains another file, `vaccines_stream.conf`. This file tells `supervisor`, a program monitoring package, how to behave. Should we want to collect tweets for a very long time, we can use `supervisor` to automatically restart the `twitter-streamer-V1.py` script in the event that it breaks.

9. To edit the `vaccines_stream.conf` file ...
    * Enter `nano ./supervisor/vaccines_stream.conf` and scroll down to the section that looks like the below:
    ```shell
    [program:vaccines_stream]
    command=python3 /home/**YOUR_USERNAME**/vaccines/v1-streaming/twitter-streamer-V1.py -cf /home/**YOUR_USERNAME**/vaccines/v1-streaming/config.ini     ; the program (relative uses PATH, can take args)
    directory=/data_volume/                                                 ; directory to cwd to before exec (def no cwd)
    autostart=true                                                          ; start at supervisord start (default: true)
    autorestart=true                                                        ; when to restart if exited after running (def: unexpected)
    user=**YOUR_USERNAME**                                                           ; setuid to this UNIX account to run the program
    stderr_logfile=/var/log/supervisor/vaccines_stream_err.log                      ; stderr log path, NONE for none; default AUTO
    stdout_logfile=/var/log/supervisor/vaccines_stream.log                          ; stdout log path, NONE for none; default AUTO
    ```
    * Again, replace `**YOUR_USERNAME**` with your own username 
    * Save this file and exit. 
10. Make sure you have supervisor installed (`sudo apt install supervisor`). Copy (using sudo) the `vaccines_stream.conf` file to `/etc/supervisor/conf.d/`
11. Then you can enter start supervisord by using `sudo systemctl start supervisor`
    * To make supervisord automatically restart use `sudo systemctl start supervisor`
    * You can use `sudo supervisorctl status` to check the status
    * You to reread your conf file use `sudo supervisorctl reread` and then `sudo supervisorctl update`.

The above command should have activated the `twitter-streamer-V1.py` script and, subsequently, our stream should have started. If no errors were returned, that is a good thing. You can check the `data_dir` path provided in step 6 above for tweets.

### Killing `supervisor` 
* If `supervisor` has been running for a while and you'd like to stop it you can run `sudo systemctl stop supervisor` and it will stop.

### `supervisor` logs/files
* Everything to do with `supervisor` is set up to use a standard systemctl supervisord deamon`.
    * The logs **for `supervisor`** can be found here: `/var/log/supervisor`
 

## Details on Collected Tweets

* All tweets are in English
* All tweet parameters are included (the Twitter V1 stream endpoint was utilized and this endpoint can deliver tweets in no other way)
* All tweets are matched to keywords/phrases based on a list which can be found here
    * Each line represents one matching keyword/phrase. That is, if one line says, "covid19 moderna" that means that both "covid19" and "moderna" must be present within the tweet in order for it to match. However, each line is entered into the search with an OR operator. For example, if one line says "vaccine" and the next line says "vaccinate" that means our collection captures tweet's which include EITHER the word "vaccine" OR "vaccinate."
    * Our intention was to capture vaccine-related covid19 conversations. Since the vast majority of vaccine-related conversation on Twitter (at this time) is likely to be covid19-related, however, covid19 conversation can be related to many other topics, we chose very broad vaccine-related terms (e.g., "vaccine", "vaccinate", "vaccination") and narrowed our covid19 related terms to be vaccine specific (e.g., "covid19 pfizer", "coronavirus moderna")
    See Twitter's documentation for details on how tweets match to each term.
