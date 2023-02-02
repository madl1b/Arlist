from flask import Flask, request, redirect, session
from arlist import userAuthorise, buildAccessToken, refreshToken, getTracks, buildPlaylist, buildPlaylistArtist

app = Flask(__name__)

app.secret_key = ""
app.config['SESSION_COOKIE_NAME'] = ""


@app.route("/")
def login():
    authURL = userAuthorise()
    return redirect(authURL)

@app.route('/authorize')
def redirectPage():
    authCode = request.args.get('code')
    session.clear()
    session['token'] = buildAccessToken(authCode=authCode)
    session['refresh_token'] = session['token']['refresh_token']
    return session['token']

# builds playlist featuring recommendations based on artist + danceability provided (0-1)
@app.route('/getPlaylist/<artistId>/<danceability>/<name>')
def buildNewPlaylist(artistId, danceability, name):
    if session.get('token') is None:
        return redirect('/')
    
    session['token'] = refreshToken(session['token'], session['refresh_token'])
    trackURIs = getTracks(artistId, danceability, session['token']['access_token'])

    return buildPlaylist(trackURIs, session['token']['access_token'], name)


@app.route('/tokenData')
def printToken():
    session['token'] = refreshToken(session['token'], session['refresh_token'])
    return session['token']['access_token']

# builds playlist featuring a random track from all releases (albums/singles) organised in 
# chronological order
@app.route('/artistPlaylist/<artistId>')
def buildArtistPlaylist(artistId):
    if session.get('token') is None:
        return redirect('/') 
    
    session['token'] = refreshToken(session['token'], session['refresh_token'])

    return buildPlaylistArtist(artistId, session['token']['access_token'])
    
      

