import click
import os
from app import create_app
from config import DevelopmentConfig, Config

config = Config if os.environ.get("RAILWAY_ENVIRONMENT") else DevelopmentConfig
app = create_app(config)


@app.cli.command("seed-admin")
def seed_admin():
    """Create the admin user (admin@admin.com / admin123)."""
    from app import db
    from app.models.user import User
    db.create_all()
    existing = User.query.filter_by(email="admin@admin.com").first()
    if existing:
        click.echo("Admin user already exists.")
        return
    user = User(email="admin@admin.com", name="Admin", role="admin")
    user.set_password("admin123")
    db.session.add(user)
    db.session.commit()
    click.echo("Admin user created: admin@admin.com / admin123")


@app.cli.command("sync-youtube")
def sync_youtube():
    """Sync hearings from YouTube channel."""
    from app.services.youtube_sync import sync_hidalgo_videos
    sync_hidalgo_videos()


if __name__ == "__main__":
    app.run()