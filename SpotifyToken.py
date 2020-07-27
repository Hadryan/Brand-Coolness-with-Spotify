#!/usr/bin/env python
# coding: utf-8

# In[1]:


import os
import sys
import spotipy
import spotipy.util as util

# In[2]:


def get_Token(scope = 'user-library-read', cid, secret, uri = 'www.google.com'):
    
    #default scope: user library
    #use your CID and Secret from the Spotify API
    #select a uri for sign in, default: google

    #sets environment variables 
    get_ipython().run_line_magic('set_env', 'SPOTIPY_CLIENT_ID = cid')
    get_ipython().run_line_magic('set_env', 'SPOTIPY_CLIENT_SECRET = secret')
    get_ipython().run_line_magic('set_env', 'SPOTIPY_REDIRECT_URI = uri')
    
    #selects username
    username = sys.argv[1]

    #returns user token
    try:
        token = util.prompt_for_user_token(username,scope,cid,secret,uri)
    except:
        os.remove(f".cache-{username}")

        token = util.prompt_for_user_token(username,scope,cid,secret,uri)

    #authorizing access to user info with token
    spotify = spotipy.Spotify(auth = token)
    
    #returns access token
    return spotify


