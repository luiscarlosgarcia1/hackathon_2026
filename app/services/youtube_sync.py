import feedparser
from youtube_transcript_api import YouTubeTranscriptApi
from app import db
from app.models.hearing import Hearing  # ← fixed
from datetime import datetime

RSS_FEED = "https://www.youtube.com/feeds/videos.xml?channel_id=UC6TaYtcc4hbJPaXt6SHmyyQ"

def sync_hidalgo_videos():
    feed = feedparser.parse(RSS_FEED)
    print(f"Feed entries found: {len(feed.entries)}")  # ← add this
    new_count = 0

    for entry in feed.entries[:5]:
        video_id = entry.get("yt_videoid") or entry.link.split("v=")[-1]
        title = entry.title
        published_at = datetime(*entry.published_parsed[:6]).date()

        if Hearing.query.filter_by(youtube_video_id=video_id).first():
            continue

        try:
            fetcher = YouTubeTranscriptApi()
            try:
                raw = fetcher.fetch(video_id)
            except:
                # Fall back to any available language (e.g. Spanish)
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