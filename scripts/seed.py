import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date
from app import create_app, db
from app.models.hearing import Hearing
from config import DevelopmentConfig

SEED_DATA = [
    {
        "title": "City Council Budget Hearing 2026",
        "date": date(2026, 2, 12),
        "transcript": (
            "The council convened to discuss the proposed FY2026 budget. "
            "Councilmember Rivera raised concerns about public transit funding cuts. "
            "The public comment period saw 14 speakers, primarily focused on housing and infrastructure."
        ),
        "agenda": "1. Call to order\n2. Budget overview presentation\n3. Department requests\n4. Public comment\n5. Adjournment",
    },
    {
        "title": "Zoning Variance Hearing — Riverside District",
        "date": date(2026, 3, 5),
        "transcript": (
            "Applicant requested a variance to construct a mixed-use building exceeding current height limits. "
            "Neighbors expressed concerns about parking and shadow impact. "
            "The board voted 4-2 to approve the variance with conditions."
        ),
        "agenda": "1. Application overview\n2. Staff report\n3. Applicant presentation\n4. Public testimony\n5. Board deliberation and vote",
    },
    {
        "title": "School Board Special Meeting — Curriculum Review",
        "date": date(2026, 4, 1),
        "transcript": (
            "The board met to review proposed changes to the K-8 science curriculum. "
            "Parents and educators submitted written comments. "
            "No vote was taken; a follow-up session was scheduled for April 22."
        ),
        "agenda": "1. Welcome\n2. Curriculum committee report\n3. Public input\n4. Next steps",
    },
]


def seed():
    app = create_app(DevelopmentConfig)
    with app.app_context():
        for data in SEED_DATA:
            exists = Hearing.query.filter_by(title=data["title"], date=data["date"]).first()
            if not exists:
                hearing = Hearing(**data)
                db.session.add(hearing)
                print(f"  Seeded: {data['title']}")
            else:
                print(f"  Skipped (already exists): {data['title']}")
        db.session.commit()
    print("Seed complete.")


if __name__ == "__main__":
    seed()
