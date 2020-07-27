#!/usr/bin/env python
# coding: utf-8

# In[1]:


import os
import sys
import spotipy
import spotipy.util as util
import pandas as pd
import numpy as np


# In[2]:


def get_Token():
    scope = 'user-library-read'
    cid = '9d655b4585c04a2fa6cae9f8c297fbd1'
    secret = '2fe8e6cf3a9244c2b2cf11a7b0851972'
    uri = 'http://google.com/'

    get_ipython().run_line_magic('set_env', 'SPOTIPY_CLIENT_ID = cid')
    get_ipython().run_line_magic('set_env', 'SPOTIPY_CLIENT_SECRET = secret')
    get_ipython().run_line_magic('set_env', 'SPOTIPY_REDIRECT_URI = uri')

    username = sys.argv[1]

    try:
        token = util.prompt_for_user_token(username,scope,cid,secret,uri)
    except:
        os.remove(f".cache-{username}")

        token = util.prompt_for_user_token(username,scope,cid,secret,uri)

    spotify = spotipy.Spotify(auth = token)
    
    return spotify


# In[3]:


def playlistParser(uri_input):
    
    '''
    FUNCTION
    ----------
    - Requests info on a playlist from the Spotify API
    - Convert retrieved data into JSON format
    - Parses the JSON file, extracting, dropping, and expanding relevant columns
    - Cleans data in each column so each inputted URI has standardized information
    
    - For list inputs:
        - Combines all playlists into a single dataframe
    - For string inputs:
        - Dataframe containing data for the single playlist input
    
    PARAMETER
    ----------
    uri_input | string or list of strings | A spotify playlist URI, or list of URI's. A URI can be obtained 
                                            through the online Spotify API, or manually copy and pasted from 
                                            the Spotify desktop app.
    
    
    RETURNS
    ----------
    A dataframe containing all relevant track info (artist, album, name, etc.) and audio features.
    Column list:
    
    ~ Main dataframe containing key ID info and basic track info
    ~ Track Info dataframe
        - Contains in-depth audio data on each track such as valence, tempo, and danceability
       
    
    '''
    
    #initializing empty dataframe
    final_tracks = pd.DataFrame()
    
    #initializing empty list for if/else loop
    uri_list = []
    
    #if input is a string, append it to an empty list
    if type(uri_input) == list:
        
        uri_list = uri_input
        
    #else, the inputted list will be used
    elif type(uri_input) == str:
        uri_list.append(uri_input)
        
    #looping through each uri in the list 
    for uri in uri_list:
        
        #assert checking if the input is a valid spotify playlist uri
        assert 'spotify:playlist:' in uri

        #requesting spotify playlist data from the spotify API
        #encoding to json with json.dumps
        #reading json data into a pandas dataframe
        main = spotify.playlist_tracks(uri, limit = 100)
        main = json.dumps(main, sort_keys = True)
        main = pd.read_json(main)

        #selecting to include only the column that contains information
        main = main[['items']]

        #opening the nested data within the items column
        #drops the nested column, converts to a series, concatenates the unnested data to the dataframe
        main = pd.concat([main.drop(columns = 'items'), main['items'].apply(pd.Series)], axis = 1)

        #selecting to include only columns with relevant data
        main = main[['added_by', 'track']]

        #unnesting the added_by column to extract data
        main = pd.concat([main.drop(columns = 'added_by'), main['added_by'].apply(pd.Series)], axis = 1)

        #accessing column that contains track info
        main = main[['track']]

        #unnesting the track column
        main = pd.concat([main.drop(columns = 'track'), main['track'].apply(pd.Series)], axis = 1)

        #dropping unneeded columns that resulted from dennesting the track column
        main = main.drop(columns = ['available_markets', 'disc_number', 'episode', 'external_ids',
                                   'external_urls', 'href', 'preview_url', 'track', 'type'])

        #renaming columns
        #future dennesting process will uncover columns with identical column names
        #renaming to ensure columns have unique names
        #"track_name" is a temporary name, will be renamed at the end
        main = main.rename(columns = {'id':'track_id','name':'track_name','uri': 'track_uri', 'artists':'artist'})

        #dennesting the album column
        main = pd.concat([main.drop(columns = 'album'), main['album'].apply(pd.Series)], axis = 1)

        #dropping unneeded columns
        main = main.drop(columns = ['artists','album_type', 'external_urls', 'href',
                                    'images', 'release_date_precision','type'])

        #renaming columns to ensure unique column
        #"album_name" is a temporary name, will be renamed at the end
        #done this way to ensure unique names during the cleaning process
        main = main.rename(columns = {'name':'album_name', 'id': 'album_id', 'uri':'album_uri'})

        #denesting the artist column
        main = pd.concat([main.drop(columns = 'artist'), main['artist'].apply(pd.Series)], axis = 1)

        #artist column produced columns with integers as its labels
        #dropping those unnecessary columns
        main = main.drop(columns = [1])

        #dennesting the column labeled "0" that resulted from the artist columns dennesting
        main = pd.concat([main.drop(columns = 0), main[0].apply(pd.Series)], axis = 1)

        #renaming columns
        main = main.rename(columns = {'id':'artist_id', 'name':'artist', 'uri':'artist_uri'})

        #Dropping unneeded columns
        main = main.drop(columns = ['href','type', 'external_urls'])

        #creating a list of track uri's
        track_uri_list = list(main['track_uri'])

        #requesting audio features for each track in the track uri list
        #reading resulting json data into a pandas dataframe
        track_feat = spotify.audio_features(track_uri_list)
        track_feat = json.dumps(track_feat, sort_keys = True)
        track_feat = pd.read_json(track_feat)

        #dropping unneeded columns
        track_feat = track_feat.drop(columns = ['analysis_url', 'duration_ms', 
                                                'track_href', 'type', 'uri'])

        #renaming the id column
        track_feat = track_feat.rename(columns = {'id':'track_id'})

        #musical key column is integer based
        #Having regular notation is more useful, so I replace the integers with their equivalent mappings
        #as defined by the spotify API documentation
        track_feat['key'] = track_feat['key'].replace({0:'C', 1:'C#', 2:'D', 3:'D#',
                                                      4:'E', 5:'F', 6:'F#', 7:'G', 
                                                      8:'G#',9:'A', 10:'A#', 11:'B'})

        #Spotify API documentation states that the mode column uses integers to denote
        #major and minor modes, I convert these to strings to increase readability
        track_feat['mode'] = track_feat['mode'].replace({0:'minor', 1:'major'})


        #renaming track_name and album_name now that future processes will not produce identical column names
        main = main.rename(columns = {'track_name':'track', 'album_name':'album'})


        #merging the tracks and track_feat dataframes on track_id
        #outer join method so all data is preserved
        tracks = pd.merge(main, track_feat, on = 'track_id', how = 'outer')

        #converting the duration_ms column to be in seconds
        #1000 milliseconds in a second
        #converting to int from float for standardization
        tracks = tracks.rename(columns = {'duration_ms':'duration_s'})
        tracks['duration_s'] = (tracks['duration_s']/1000).astype(int)
                       
        #concatenating each track dataframe
        final_tracks = pd.concat([final_tracks, tracks])
        
    #returns the dataframe with columns in the following order
    return final_tracks[['artist_uri', 'artist_id', 'album_uri', 'album_id', 'track_uri', 'track_id',
                         'artist', 'track', 'album', 'release_date', 'track_number',
                         'is_local', 'popularity', 'explicit', 'key', 'mode', 'time_signature', 'tempo',
                         'duration_s','energy', 'liveness', 'speechiness', 'valence', 'acousticness', 'loudness', 
                         'danceability', 'instrumentalness']]


# In[ ]:




