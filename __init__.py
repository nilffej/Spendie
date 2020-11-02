import tekore as tk

from flask import Flask, request, redirect, session, render_template, jsonify, make_response
from pprint import pprint

from lyricscraper import search_lyrics
from config import *

conf = (CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)
cred = tk.Credentials(*conf)
spotify = tk.Spotify()

users = {}
auths = {}

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chicken'
playbackdata = {}



def get_user_data():
    user = spotify.current_user()
    if not len(user.images):
        pfp = "https://vignette.wikia.nocookie.net/caramella-girls/images/9/99/Blankpfp.png/revision/latest?cb=20190122015011"
    else:
        pfp = user.images[0].url
    data = {
        'pfp':pfp,
        'name':user.display_name,
        'data':[
            ('Followers',user.followers.total),
            ('Country',user.country),
            ('Email',user.email)
        ],
        'url':user.external_urls['spotify']
    }
    return data

def get_playback_data(token):
    tempspotify = tk.Spotify()
    with tempspotify.token_as(token):
        data = { 'isPlaying': False }
        recenttracks = []
        for item in tempspotify.playback_recently_played(limit=6).items:
            recenttracks.append(get_track_data(item.track))
        if not len(recenttracks):
            data['maintrack'] = False
        data['recent'] = recenttracks
        current = tempspotify.playback_currently_playing()
        if current and current.currently_playing_type == 'track':
            data['maintrack'] = get_track_data(current.item)
            data['isPlaying'] = True
        else:
            data['maintrack'] = data['recent'][0]
            data['recent'].pop(0)
        print(tempspotify.current_user().display_name + ": " + data['maintrack']['title'] + " - " + data['maintrack']['artists'])
        # print('\n')
        return data



# GETTING TOP TRACKS DATA

def get_top_tracks(term):
    data = []
    toptracks = spotify.current_user_top_tracks(time_range=term,limit=50)
    for item in toptracks.items:
        data.append(get_track_data(item))
    return data

def get_track_data(track):
    if not len(track.album.images):
        pfp = "https://vignette.wikia.nocookie.net/caramella-girls/images/9/99/Blankpfp.png/revision/latest?cb=20190122015011"
    else:
        pfp = track.album.images[0].url
    data = {
        'image':pfp,
        'title':track.name,
        'artists':get_track_artists(track.artists),
        'album':track.album.name,
        'url':track.external_urls['spotify']
    }
    return data

def get_track_artists(item):
    artistlist = ''
    for artist in item:
        artistlist += artist.name + ', '
    return artistlist[:-2]



# GETTING TOP ARTISTS DATA

def get_top_artists(term):
    data = []
    topartists = spotify.current_user_top_artists(time_range=term,limit=50)
    for item in topartists.items:
        data.append(get_artist_data(item))
    return data

def get_artist_data(artist):
    if not len(artist.images):
        pfp = "https://vignette.wikia.nocookie.net/caramella-girls/images/9/99/Blankpfp.png/revision/latest?cb=20190122015011"
    else:
        pfp = artist.images[0].url
    data = {
        'image':pfp,
        'name':artist.name,
        'url':artist.external_urls['spotify']
    }
    return data

def tokencheck(sessionid):
    token = users.get(sessionid, None)
    if token is None:
        session.pop('user', None)
        return render_template('index.html')
    if token.is_expiring:
        token = cred.refresh(token)
        users[sessionid] = token
    # print('TOKEN RETRIEVED FOR: ' + user) 
    return token



# MAIN APP

@app.route('/error')
def error():
    return render_template('error.html')

@app.route('/', methods=['GET'])
def main():
    # try:
    print(session)
    user = session.get('user', None)
    token = users.get(user, None)
    page = ''

    if user is None or token is None:
        session.pop('user', None)
        return render_template('index.html')

    if token.is_expiring:
        token = cred.refresh(token)
        users[user] = token

    with spotify.token_as(users[user]):
        print("LOGIN: " + spotify.current_user().display_name)
        print(session)
        pprint(users.keys())

        userdata = get_user_data()
        playbackdata = get_playback_data(users[user])

        monthtracks = get_top_tracks('short_term')
        yeartracks = get_top_tracks('medium_term')
        alltimetracks = get_top_tracks('long_term')

        monthartists = get_top_artists('short_term')
        yearartists = get_top_artists('medium_term')
        alltimeartists = get_top_artists('long_term')


        return render_template('homepage.html', user=userdata,
                    playback=playbackdata, month_tracks=monthtracks,
                    year_tracks=yeartracks, alltime_tracks=alltimetracks,
                    month_artists=monthartists, year_artists=yearartists,
                    alltime_artists=alltimeartists, sessionid=session['user'])
    return page
    # except:
    #     return render_template('error.html')

@app.route('/login', methods=['GET'])
def login():
    if 'user' in session:
        return redirect('/', 307)

    scope = tk.scope.read
    auth = tk.UserAuth(cred, scope=scope)
    auths[auth.state] = auth
    return redirect(auth.url, 307)

@app.route('/callback', methods=['GET'])
def login_callback():
    code = request.args.get('code', None)
    state = request.args.get('state', None)
    auth = auths.pop(state, None)

    if auth is None:
        return 'Invalid state!', 400

    try:
        token = auth.request_token(code, state)
        session['user'] = state
        users[state] = token
    except:
        redirect('/')
    return redirect('/', 307)

@app.route('/logout', methods=['GET'])
def logout():
    pprint(users.keys())
    uid = session.pop('user', None)
    if uid is not None:
        users.pop(uid, None)
    return redirect('/', 307)

@app.route('/updatePlayback/<sessionid>', methods=['POST'])
def updatePlaybackData(sessionid):
    data = {}
    # print(sessionid)
    try:
        token = tokencheck(sessionid)
        with spotify.token_as(token):
            # print(spotify.current_user().display_name + ' ' + session['user'])
            try:
                    data = get_playback_data(token)
                    return make_response(jsonify(data), 200)
            except:
                print("ERROR REACHED: " + spotify.current_user().display_name)
                print(session)
                return(jsonify({}), 400)
    except:
        print("REFRESH REQUIRED: " + sessionid)
        return(jsonify({}), 400)


@app.route('/loadLyrics', methods=['POST'])
def lyric_search():
    req = request.get_json()
    lyrics = search_lyrics(req['title'],req['artists'])
    return make_response(jsonify(lyrics), 200)


if __name__ == '__main__':
    app.debug = True
    app.run(threaded=True)