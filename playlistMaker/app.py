from flask import Flask, request, redirect, session
from arlist import userAuthorise, buildAccessToken, refreshToken, getTracks, buildPlaylist, buildPlaylistArtist, searchSampleSong
from samples import initialize_database

app = Flask(__name__)

app.secret_key = "123400:dasd"
app.config['SESSION_COOKIE_NAME'] = 'cookie'


def handleToken():
    session['token'] = refreshToken(session['token'], session['refresh_token'])


@app.route("/")
def login():
    authURL = userAuthorise()
    return redirect(authURL)

@app.route('/authorize')
def redirectPage():
    authCode = request.args.get('code')
    session.clear()
    session.permanent = True
    session['token'] = buildAccessToken(authCode=authCode)
    session['refresh_token'] = session['token']['refresh_token']
    return 'authorised!'


@app.route('/getPlaylist/<artistId>/<danceability>/<name>')
def buildNewPlaylist(artistId, danceability, name):
    if session.get('token') is None:
        return redirect("/")
    handleToken()
    trackURIs = getTracks(artistId, danceability, session['token']['access_token'])

    return buildPlaylist(trackURIs, session['token']['access_token'], name)


@app.route('/tokenData')
def printToken():
    if session.get('token') is None:
        return redirect("/")
    session['token'] = refreshToken(session['token'], session['refresh_token'])
    return session['token']
 

@app.route('/artistPlaylist/<artistId>')
def buildArtistPlaylist(artistId):
    if session.get('token') is None:
        return redirect("/")
    handleToken()

    return buildPlaylistArtist(artistId, session['token']['access_token'])
    


@app.route('/sampleSearch/<years>/<genre>')
def searchSample(years, genre):
    if session.get('token') is None:
        return redirect("/")
    handleToken()

    return searchSampleSong(years, genre, session['token']['access_token'])


if __name__ == "__main__":
    app.debug = True
    initialize_database()
    app.run()



    
