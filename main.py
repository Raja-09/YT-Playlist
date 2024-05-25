import os

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import pickle


scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
api_service_name = "youtube_music"
api_version = "v3"
client_secrets_file = "secret.json"  # Replace with your client secrets file
credentials_file = "credentials.pkl"

try:
    with open(credentials_file, "rb") as f:
        credentials = pickle.load(f)
except FileNotFoundError:
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, scopes
    )
    credentials = flow.run_local_server(port=0)
    with open(credentials_file, "wb") as f:
        pickle.dump(credentials, f)

youtube = googleapiclient.discovery.build(
    api_service_name, api_version, credentials=credentials
)


def getDetailsFromFile():
    with open("details.txt", "r") as file:
        details = {}
        playlist = ""
        for line in file:
            if line[0] == "#":
                playlist = line[1:].strip()
                details[playlist] = []
            else:
                details[playlist].append(line.strip())
    return details


def getSong(search_query):
    youtube = googleapiclient.discovery.build("youtube", "v3", credentials=credentials)
    search_response = (
        youtube.search().list(q=search_query, part="snippet", maxResults=1).execute()
    )

    search_result = search_response["items"][0]
    video_id = search_result["id"]["videoId"]
    return video_id


def getOrCreatePlaylist(playlist_name):
    playlist_response = youtube.playlists().list(part="snippet", mine=True).execute()
    playlist_id = None
    for playlist in playlist_response["items"]:
        if playlist["snippet"]["title"] == playlist_name:
            playlist_id = playlist["id"]
            break
    if playlist_id is None:
        playlist_response = (
            youtube.playlists()
            .insert(part="snippet", body={"snippet": {"title": playlist_name}})
            .execute()
        )
        playlist_id = playlist_response["id"]
    return playlist_id


def addSongToPlaylist(playlist_id, video_id):
    youtube.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": playlist_id,
                "position": 0,
                "resourceId": {"kind": "youtube#video", "videoId": video_id},
            }
        },
    ).execute()


def getPlaylistSongs(playlist_name):
    playlist_id = getOrCreatePlaylist(playlist_name)
    playlist_response = (
        youtube.playlistItems()
        .list(part="snippet", playlistId=playlist_id, maxResults=50)
        .execute()
    )
    return playlist_response


def main():

    details = getDetailsFromFile()
    for playlist, songs in details.items():
        playlist_id = getOrCreatePlaylist(playlist)
        for song in songs:
            video_id = getSong(song)
            addSongToPlaylist(playlist_id, video_id)


if __name__ == "__main__":
    main()
