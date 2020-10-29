import tekore as tk

from flask import Flask, request, redirect, session, render_template
from pprint import pprint

from config import *

conf = (CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)
cred = tk.Credentials(*conf)
spotify = tk.Spotify()

users = {}
auths = {}

def debug(object):
    pprint(type(object))
    pprint(object)
    return

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
        'uri':user.external_urls['spotify']
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

def get_tracks_month():
    data = []
    toptracks = spotify.current_user_top_tracks(time_range='short_term',limit=50)
    for item in toptracks.items:
        data.append(get_track_data(item))
    return data

def get_tracks_year():
    data = []
    toptracks = spotify.current_user_top_tracks(time_range='medium_term',limit=50)
    for item in toptracks.items:
        data.append(get_track_data(item))
    return data

def get_tracks_alltime():
    data = []
    toptracks = spotify.current_user_top_tracks(time_range='long_term',limit=50)
    for item in toptracks.items:
        data.append(get_track_data(item))
    return data

def get_track_data(track):
    data = {
        'image':track.album.images[0].url,
        'title':track.name,
        'artists':get_artists(track.artists),
        'album':track.album.name,
        'uri':track.external_urls['spotify'],
    }
    return data

def get_artists(item):
    artistlist = ''
    for artist in item:
        artistlist += artist.name + ', '
    return artistlist[:-2]

def app_factory() -> Flask:
    app = Flask(__name__)
    app.debug = True
    app.config['SECRET_KEY'] = 'aliens'

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
            monthtracks = get_tracks_month()
            yeartracks = get_tracks_year()
            alltimetracks = get_tracks_alltime()
            
            return render_template('homepage.html', user=userdata,
                        playback=playbackdata, month_tracks=monthtracks,
                        year_tracks=yeartracks, alltime_tracks=alltimetracks)

        return page

    @app.route('/login', methods=['GET'])
    def login():
        if 'user' in session:
            return redirect('/', 307)

        scope = tk.scope.every
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

    return app


if __name__ == '__main__':
    application = app_factory()
    application.run('127.0.0.1', 5000)