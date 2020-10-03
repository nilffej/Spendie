import tekore as tk

from tekore.scope import every
from flask import Flask, request, redirect, session, render_template
from pprint import pprint

from config import *

conf = (CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)
cred = tk.Credentials(*conf)
spotify = tk.Spotify()

users = {}

app = Flask(__name__)

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
            ('Email',user.email),
            ('Account Type',user.product.capitalize())
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

def get_top_tracks():
    data = []
    toptracks = spotify.current_user_top_tracks(time_range='short_term',limit=50)
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
    app.config['SECRET_KEY'] = 'aliens'

    @app.route('/', methods=['GET'])
    def main():
        user = session.get('user', None)
        page = ''

        if user is not None:
            token = users[user]

            if token.is_expiring:
                token = cred.refresh(token)
                users[user] = token

            with spotify.token_as(users[user]):
                userdata = get_user_data()
                playbackdata = get_playback_data()
                toptracksdata = get_top_tracks()

                return render_template('homepage.html', user=userdata,
                            playback=playbackdata, toptracks=toptracksdata)

        return render_template('index.html', page=page)

    @app.route('/login', methods=['GET'])
    def login():
        auth_url = cred.user_authorisation_url(scope=every)
        return redirect(auth_url, 307)

    @app.route('/callback', methods=['GET'])
    def login_callback():
        code = request.args.get('code', None)

        token = cred.request_user_token(code)
        with spotify.token_as(token):
            info = spotify.current_user()

        session['user'] = info.id
        users[info.id] = token

        return redirect('/', 307)

    @app.route('/logout', methods=['GET'])
    def logout():
        uid = session.pop('user', None)
        if uid is not None:
            users.pop(uid, None)
        return redirect('/', 307)

    return app


if __name__ == '__main__':
    app.debug = True
    application = app_factory()
    application.run('127.0.0.1', 5000)