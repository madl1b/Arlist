import json 
import requests 
import base64
import time
import random
import operator

# Client Keys
clientID = "YOUR CLIENT ID"
clientSecret = "YOUR CLIENT SECRET"

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




    