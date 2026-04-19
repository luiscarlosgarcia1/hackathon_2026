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
YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/search"

print("youtube_sync file is loading")


def get_channel_videos(max_results=15):
    params = {
        "key": YOUTUBE_API_KEY,
        "channelId": CHANNEL_ID,
        "part": "snippet",
        "order": "date",
        "type": "video",
        "maxResults": max_results,
    }
    response = requests.get(YOUTUBE_API_URL, params=params)
    data = response.json()

    if "error" in data:
        print(f"YouTube API error: {data['error']['message']}")
        return []

    videos = []
    for item in data.get("items", []):
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
        published_at = datetime.fromisoformat(
            item["snippet"]["publishedAt"].replace("Z", "+00:00")
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