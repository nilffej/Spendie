from bs4 import BeautifulSoup
import requests

def search_lyrics(song, artist):
    if '(' in song:
        song = song[:song.find('(')]
    if ',' in artist:
        artist = artist[:artist.find(',')]
    s = song + ' ' + artist
    searchquery = '+'.join(s.split())

    searchurl = requests.get(f'https://search.azlyrics.com/search.php?q={searchquery}').text
    results = BeautifulSoup(searchurl, 'lxml')
    print(f'https://search.azlyrics.com/search.php?q={searchquery}')

    try:
        firstresult = results.find_all('tr')
        temp = firstresult[0].find('td')
        for child in temp:
            if child.name and child.has_attr('class') and 'btn' in child['class']:
                temp = firstresult[1].find('td')
        lyricslink = temp.find('a')['href']

        lyrurl = requests.get(lyricslink).text
        lyrbody = BeautifulSoup(lyrurl, 'lxml')

        bodydiv = lyrbody.find_all(class_="col-xs-12 col-lg-8 text-center")
        divs = bodydiv[0].find_all("div")
        return str(divs[5])
    except:
        return "<div>Lyrics not found!</div>"
        pass
    