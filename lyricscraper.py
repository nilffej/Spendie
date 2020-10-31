from bs4 import BeautifulSoup
import requests

def search_lyrics(song, artist):
    # Reformats song and artist for search
    if '(' in song:
        song = song[:song.find('(')]
    if ',' in artist:
        artist = artist[:artist.find(',')]
    song = ''.join(c for c in song if not isSpecial(c))
    artist = ''.join(c for c in artist if not isSpecial(c))

    s = song + ' ' + artist
    searchquery = '+'.join(s.split())

    searchurl = requests.get(f'https://search.azlyrics.com/search.php?q={searchquery}').text
    results = BeautifulSoup(searchurl, 'lxml')
    # print(f'https://search.azlyrics.com/search.php?q={searchquery}')

    try:
        firstresult = results.find_all('tr')
        temp = firstresult[0].find('td')
        
        # Checks if first list item on search results is buttons and not a lyric result
        for child in temp:
            if child.name and child.has_attr('class') and 'btn' in child['class']:
                temp = firstresult[1].find('td')
        lyricslink = temp.find('a')['href']

        lyrurl = requests.get(lyricslink).text
        lyrbody = BeautifulSoup(lyrurl, 'lxml')

        # Locate div that contains lyrics
        bodydiv = lyrbody.find_all(class_="col-xs-12 col-lg-8 text-center")
        divs = bodydiv[0].find_all("div")
        data = {
            'lyrics':str(divs[5]),
            'source':lyricslink
        }
        return data
    except:
        if artist != '':
            search_lyrics(song, '')
        data = {
            'lyrics':'<div>Lyrics not found!</div>',
            'source':''
        }
        return data

def isSpecial(chr):
    return chr in "\"@#$%^&()"

# search_lyrics('CUT EM IN','Anderson .Paak')