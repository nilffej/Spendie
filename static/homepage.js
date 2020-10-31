var interval = setInterval(updatePlaybackData, 5000);

function updatePlaybackData() {
    fetch(`${window.origin}/updatePlayback`, {
        method: "POST",
        credentials: "include",
        cache: "no-cache",
        headers: new Headers({
            "content-type": "application/json"
        })
    })
        .then(function (response) {
            if (response.status != 200) {
                console.log(`Error: ${response.status}`);
                return;
            }
            response.json().then(function (data) {
                pbcard = document.getElementById("playbackCard");
                if (data["isPlaying"]) document.getElementById("playStatus").innerHTML = "Currenlty Playing";
                else { document.getElementById("playStatus").innerHTML = "Last Played"; }
                if (data["maintrack"]["title"] != playback["maintrack"]["title"]) {
                    playback["maintrack"] = data["maintrack"];
                    document.getElementById("mainTrack").innerHTML = `
                    <a href="${playback['maintrack']['url']}"><img src="${playback['maintrack']['image']}" style="height: 250px; width: 250px;"></a>
                    <div style="padding-left: 20px; display: flex; flex-direction: column;">
                        <h4 style="max-width: 400px;">${playback['maintrack']['title']}</h4>
                        <p style="padding-top: 10px;">
                            ${playback['maintrack']['artists']}<br>
                            ${playback['maintrack']['album']}
                        </p>
                    </div>
                    `;
                    lyrbutt = document.getElementById("lyricsButton");
                    if (lyrbutt.innerHTML == 'Close Lyrics') loadLyrics();
                    else { 
                        lyrbutt.innerHTML = `Find Lyrics For ${playback['maintrack']['title']}`;
                    }
                    
                }
                if (data["recent"][0]["title"] != playback["recent"][0]["title"]) {
                    playback["recent"] = data["recent"];
                    recent = document.getElementById("recentTracks");
                    recent.innerHTML = "";
                    for (i = 0; i < playback["recent"].length - 1; i++) {
                        recent.innerHTML += `
                    <a href="${playback['recent'][i]['url']}">
                        <img src="${playback['recent'][i]['image']}" style="height: 80px; width: 80px; margin-right: 5px; margin-bottom: 5px;">
                    </a>
                    `
                    }
                }
            });
        })
}

function loadLyrics() {
    fetch(`${window.origin}/loadLyrics`, {
        method: "POST",
        credentials: "include",
        cache: "no-cache",
        headers: new Headers({
            "content-type": "application/json"
        }),
        body: JSON.stringify({
            title: playback['maintrack']['title'],
            artists: playback['maintrack']['artists']
        })
    })
        .then(function (response) {
            if (response.status != 200) {
                console.log(`Error: ${response.status}`);
                return;
            }
            console.log(response)
            response.json().then(function (data) {
                lyrbutt = document.getElementById("lyricsButton")
                lyrbutt.innerHTML = 'Close Lyrics';
                lyrbutt.setAttribute("onClick", "closeLyrics()");
                lyrics = document.getElementById("lyrics");
                lyrics.parentElement.style["padding-top"] = "10px";
                lyrics.innerHTML = data;
                lyrics.style["padding"] = "10px";
            });
        });
}

function closeLyrics() {
    lyrbutt = document.getElementById("lyricsButton");
    lyrbutt.innerHTML = `Find Lyrics For ${playback['maintrack']['title']}`;
    lyrbutt.setAttribute("onClick", "loadLyrics()");
    lyrics = document.getElementById("lyrics");
    lyrics.parentElement.style["padding-top"] = "0px";
    lyrics.innerHTML = '';
    lyrics.style["padding"] = "0px";
}

function changeTab(obj) {
    tabs = obj.parentElement.children;
    for (i = 0; i < tabs.length; i++) {
        tabs[i].className = tabs[i].className.replace(" active", "")
    }
    obj.className += " active";
    if (obj.parentElement.id == "trackTab") {
        changeTrackTabContent(obj.id)
    }
    if (obj.parentElement.id == "artistTab") {
        changeArtistTabContent(obj.id)
    }
}

function changeTrackTabContent(obj_id) {
    l = eval(obj_id);
    table = document.getElementById("trackTable");
    table.innerHTML = ""
    for (i = 0; i < l.length; i++) {
        newcell = table.insertRow();
        newcell.innerHTML = `
        <tr>
            <td>${i + 1}</td>
            <td><a href="${l[i]['url']}"><img src="${l[i]['image']}" style="height: 60px; width: 60px;"></a></td>
            <td>
                <h6>${l[i]['title']}</h6>
                <p style="margin-top: -10px;">${l[i]['artists']}</p>
            </td>
        </tr>
        `;
    }
}

function changeArtistTabContent(obj_id) {
    l = eval(obj_id);
    table = document.getElementById("artistTable");
    table.innerHTML = ""
    for (i = 0; i < l.length; i++) {
        newcell = table.insertRow();
        newcell.innerHTML = `
        <tr>
            <td width="40px">${i + 1}</td>
            <td width="60px"><a href=" ${l[i]['url']}"><img src="${l[i]['image']}" style="height: 60px; width: 60px;"></a></td>
            <td>
                <p>${l[i]['name']}</p>
            </td>
        </tr>
        `;
    }
}