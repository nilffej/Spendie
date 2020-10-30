import tekore as tk

from flask import Flask, request, redirect, session, render_template, jsonify, make_response
from pprint import pprint
import urllib.request, json

from config import *

conf = (CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)
cred = tk.Credentials(*conf)
spotify = tk.Spotify()

users = {}
auths = {}



def get_user_data():
    user = spotify.current_user()
    data = {
        'pfp':user.images[0].url,
        'name':user.display_name,
        'data':[
            ('Followers',user.followers.total),
            ('Country',user.country),
            ('Email',user.email)
        ],
        'url':user.external_urls['spotify']
    }
    return data

def get_playback_data():
    data = { 'isPlaying': False }
    recenttracks = []
    for item in spotify.playback_recently_played(limit=6).items:
        recenttracks.append(get_track_data(item.track))
    data['recent'] = recenttracks
    current = spotify.playback_currently_playing()
    if current:
        data['isPlaying'] = True
        data['maintrack'] = get_track_data(current.item)
    else:
        data['maintrack'] = data['recent'][0]
        data['recent'].pop(0)
    return data



# GETTING TOP TRACKS DATA

def get_top_tracks(term):
    data = []
    toptracks = spotify.current_user_top_tracks(time_range=term,limit=50)
    for item in toptracks.items:
        data.append(get_track_data(item))
    return data

def get_track_data(track):
    data = {
        'image':track.album.images[0].url,
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
    data = {
        'image':artist.images[0].url,
        'name':artist.name,
        'type':artist.type,
        'url':artist.external_urls['spotify']
    }
    return data



# LYRICS SEARCHER



# MAIN APP

def app_factory() -> Flask:
    app = Flask(__name__)
    app.debug = True
    app.config['SECRET_KEY'] = 'aliens'
    playbackdata = {}

    @app.route('/', methods=['GET'])
    def main():
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
            userdata = get_user_data()
            playbackdata = get_playback_data()

            monthtracks = get_top_tracks('short_term')
            yeartracks = get_top_tracks('medium_term')
            alltimetracks = get_top_tracks('long_term')

            monthartists = get_top_artists('short_term')
            yearartists = get_top_artists('medium_term')
            alltimeartists = get_top_artists('long_term')
            
            print(playbackdata['maintrack'])

            return render_template('homepage.html', user=userdata,
                        playback=playbackdata, month_tracks=monthtracks,
                        year_tracks=yeartracks, alltime_tracks=alltimetracks,
                        month_artists=monthartists, year_artists=yearartists,
                        alltime_artists=alltimeartists)

        return page

    @app.route('/login', methods=['GET'])
    def login():
        if 'user' in session:
            return redirect('/', 307)

        scope = tk.scope.read
        auth = tk.UserAuth(cred, scope)
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
        uid = session.pop('user', None)
        if uid is not None:
            users.pop(uid, None)
        return redirect('/', 307)

    @app.route('/updatePlayback', methods=['POST'])
    def updatePlaybackData():
        user = session.get('user', None)
        with spotify.token_as(users[user]):
            data = get_playback_data()
            return make_response(jsonify(data), 200)

    return app


if __name__ == '__main__':
    application = app_factory()
    application.run('127.0.0.1', 5000)