print("TEST STARTED")
 
from app import create_app
from config import Config
from app.models.hearing import Hearing
from app.services.youtube_sync import sync_hidalgo_videos
 
app = create_app(Config)
 
print("APP CREATED SUCCESSFULLY")
 
with app.app_context():
    print("\n--- Running sync ---")
    sync_hidalgo_videos()
 
    print("\n--- All Hearings in DB ---")
    hearings = Hearing.query.all()
 
    if not hearings:
        print("No hearings found in the database.")
    else:
        for h in hearings:
            print(f"""
ID            : {h.id}
Title         : {h.title}
Date          : {h.date}
YouTube ID    : {h.youtube_video_id}
Transcript    : {"Yes ✓" if h.transcript else "None ✗"}
-------------------------------------------""")
 
        print(f"\nTotal hearings: {len(hearings)}")