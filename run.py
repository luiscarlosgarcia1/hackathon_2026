import click
from app import create_app
from config import DevelopmentConfig

app = create_app(DevelopmentConfig)


@app.cli.command("seed-admin")
def seed_admin():
    """Create the admin user (admin@admin.com / admin123)."""
    from app import db
    from app.models.user import User
    existing = User.query.filter_by(email="admin@admin.com").first()
    if existing:
        click.echo("Admin user already exists.")
        return
    user = User(email="admin@admin.com", name="Admin", role="admin")
    user.set_password("admin123")
    db.session.add(user)
    db.session.commit()
    click.echo("Admin user created: admin@admin.com / admin123")


if __name__ == "__main__":
    app.run()
