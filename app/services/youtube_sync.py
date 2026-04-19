import os
import requests
from youtube_transcript_api import YouTubeTranscriptApi
from app import db
from app.models.hearing import Hearing
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_ID = "UC6TaYtcc4hbJPaXt6SHmyyQ"

print("youtube_sync file is loading")

def get_channel_videos(max_results=15):
    channel_resp = requests.get(
        "https://www.googleapis.com/youtube/v3/channels",
        params={
            "key": YOUTUBE_API_KEY,
            "id": CHANNEL_ID,
            "part": "contentDetails",
        }
    ).json()

    uploads_playlist_id = channel_resp["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    
    playlist_resp = requests.get(
        "https://www.googleapis.com/youtube/v3/playlistItems",
        params={
            "key": YOUTUBE_API_KEY,
            "playlistId": uploads_playlist_id,
            "part": "snippet",
            "maxResults": max_results,
        }
    ).json()

    videos = []
    for item in playlist_resp.get("items", []):
        snippet = item["snippet"]
        video_id = snippet["resourceId"]["videoId"]
        title = snippet["title"]
        published_at = datetime.fromisoformat(
            snippet["publishedAt"].replace("Z", "+00:00")
        ).date()
        videos.append({
            "video_id": video_id,
            "title": title,
            "published_at": published_at,
        })

    return videos


def sync_hidalgo_videos():
    print("FUNCTION EXISTS")
    videos = get_channel_videos(max_results=15)
    print(f"Videos found: {len(videos)}")
    for v in videos:
        print(f"  Playlist: {v['title']} | {v['video_id']}")
    new_count = 0

    for video in videos:
        video_id = video["video_id"]
        title = video["title"]
        published_at = video["published_at"]

        if Hearing.query.filter_by(youtube_video_id=video_id).first():
            print(f"Already exists, skipping: {video_id}")
            continue

        try:
            fetcher = YouTubeTranscriptApi()
            try:
                raw = fetcher.fetch(video_id)
            except Exception:
                raw = fetcher.fetch(video_id, languages=['es', 'en'])
            transcript_text = " ".join([t.text for t in raw])
            print(f"Transcript fetched for {video_id} ✓")
        except Exception as e:
            print(f"No transcript for {video_id}: {type(e).__name__}: {e}")
            transcript_text = None

        hearing = Hearing(
            title=title,
            date=published_at,
            transcript=transcript_text,
            youtube_video_id=video_id
        )
        db.session.add(hearing)
        new_count += 1
        print(f"Added: {title}")

    db.session.commit()
    print(f"Sync complete. {new_count} new videos added.")