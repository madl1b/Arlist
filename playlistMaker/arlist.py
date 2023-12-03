import json 
import requests 
import base64
import time
import random
import operator
import sqlite3 as sl

# Client Keys
# ADD YOUR OWN
clientID = ""
clientSecret = ""

#Spotify URLS
spotifyAuthURL = "https://accounts.spotify.com/authorize"
spotifyTokenURL = "https://accounts.spotify.com/api/token"
spotifyRecsURL = "https://api.spotify.com/v1/recommendations"
myURL = "https://api.spotify.com/v1/me"

apiURL = "https://api.spotify.com"
redirectURI = "http://127.0.0.1:5000"

scope = "playlist-modify-public playlist-modify-private"
state = ""
show_dialogue = True
region = "AU"


def userAuthorise():
    requestArgs = {
        'client_id': clientID,
        'response_type': "code", 
        'redirect_uri': redirectURI + "/authorize",
        'scope': scope, 
        'show_dialog': True
    }
    authURL = spotifyAuthURL + "/?" + ''.join(f"&{key}={val}" for key,val in requestArgs.items())

    return authURL


def buildAccessToken(authCode):
    requestArgs = {
        'grant_type': 'authorization_code',
        'code': str(authCode),
        'redirect_uri': redirectURI + "/authorize"
    }
    return makeTokenRequest(requestArgs)

def refreshToken(token, refreshToken):
    if token['expire_time'] - time.time() < 60:
        return buildRefreshedAccessToken(refreshToken)    
    return token

def buildRefreshedAccessToken(refreshToken):
    requestArgs = {
        'grant_type': 'refresh_token',
        'refresh_token': refreshToken
    }
    return makeTokenRequest(requestArgs)

def getTracks(artistId, danceability, token):
    requestArgs = {
        'seed_artists': artistId, 
        'target_danceability': danceability,
        'limit': 50
    }
    response = requests.get(spotifyRecsURL, params=requestArgs, headers=header(token))
    trackData = response.json() 

    return [track['uri'] for track in trackData['tracks']]


def getUserId(token):
    response = requests.get(myURL, headers=header(token))
    user = response.json()
    return user['id']


def buildPlaylist(trackIds, token, name):
    userId = getUserId(token)
    url = f"https://api.spotify.com/v1/users/{userId}/playlists"

    args = {
        'name': name,
        'description': "PYTHON SPOTIFY WOOOOOOOOOOOO"
    }
    response = requests.post(url, data=json.dumps(args), headers=header(token))   
    playlistId = response.json()['id']
    trackArgs = {
        'uris': trackIds
    }
    response = requests.post(f"https://api.spotify.com/v1/playlists/{playlistId}/tracks", data=json.dumps(trackArgs), headers=header(token))   
    return response.json()

def header(token):
    return {
        'Authorization': f"Bearer {token}",
        'Content-Type': "application/json"
    }

def makeTokenRequest(params):
    encodedString = base64.b64encode(f"{clientID}:{clientSecret}".encode('ascii')).decode('ascii')
    header = {
        'Authorization': f"Basic {encodedString}",
        'Content-Type': "application/x-www-form-urlencoded"
    }
    response = requests.post(spotifyTokenURL, data=params, headers=header)
    tokenData = response.json()
    # tokenData['expire_time'] = time.time() + tokenData['expires_in']
    tokenData['expire_time'] = time.time() + tokenData['expires_in']
    return tokenData


def buildPlaylistArtist(artistId, token):
    nameData = requests.get(f"https://api.spotify.com/v1/artists/{artistId}", headers=header(token))
    name = nameData.json()['name']
    args = {
        'include_groups': "album,single",
        'limit': 50,
        'market': region,
        'offset': 0
    }
    response = requests.get(f"https://api.spotify.com/v1/artists/{artistId}/albums", params=args, headers=header(token))
    albumData = response.json()
    # get album ids then sort by oldest first
    albums = [{'id': album['id'], 'date': album['release_date']} for album in albumData['items']]
    albums.sort(key=operator.itemgetter('date'))

    # get a random track from each album, random offset based on total size
    trackIds = []
    for x in albums:
        response = requests.get(f"https://api.spotify.com/v1/albums/{x['id']}/tracks",
            params={
                'limit': 50,
                'market': region,
            },
            headers=header(token)
        )
        albumInfo = response.json()
        size = albumInfo['total']
        response = requests.get(f"https://api.spotify.com/v1/albums/{x['id']}/tracks",
            params={
                'limit': 1,
                'market': region,
                'offset': random.randint(0, size - 1) 
            },
            headers=header(token)
        )
        albumNarrowed = response.json()
        trackIds.append(albumNarrowed['items'][0]['uri'])

    return buildPlaylist(trackIds, token, name + " Arlist")

def addEntries(features, trackData):
    conn = sl.connect('samples.db')
    c = conn.cursor()

    for feature in features:
        c.execute("""
        INSERT INTO samples (id, album, name, instrumentality, acousticness, danceability, album_id)
        VALUES (?, 'an album :D', ?, ?, ?, ?, ?)        
        """, (feature['id'], trackData[feature['id']][0], feature['instrumentalness'], feature['acousticness'], 
              feature['danceability'], trackData[feature['id']][1]))

    c.execute("SELECT * FROM samples")
    rows = c.fetchall()
    conn.close()
    return rows


def searchSampleSong(years, genre, token):
    searchURL = "https://api.spotify.com/v1/search"
    # hipster tag only available for albums
    args = {
        'q': f"year={years} tag:hipster",
        'type': "album",
    }
    albums = requests.get(f"https://api.spotify.com/v1/search", params=args, headers=header(token)).json()

    # get album ids, add to query.

    albumNames = [album['id'] for album in albums['albums']['items']]
    allFeatures = []
    for name in albumNames:

        args2 = {
            'q': f"name={name} genre={genre}",
            'type': "track",
        }
        tracks = requests.get(f"https://api.spotify.com/v1/search", params=args2, headers=header(token)).json()

        track_dict = {track['id']: [track['name'], name] for track in tracks['tracks']['items']}
        trackIds = list(track_dict.keys())
        f_args = {
            'ids': ','.join(trackIds)
        }
        features = requests.get(f"https://api.spotify.com/v1/audio-features", params=f_args, headers=header(token)).json()
        allFeatures += features['audio_features']
        addEntries(features['audio_features'], track_dict)


    return allFeatures
