from app import db
from app.models.comment_cluster import CommentCluster
from app.models.public_comment import PublicComment
from app.services.clustering_service import cluster_comments
from app.services.hearing_service import get_hearing
import sqlalchemy as sa

def run_clustering(hearing_id: int) -> list[CommentCluster]:
    hearing = get_hearing(hearing_id)
    if hearing is None:
        raise LookupError(f"hearing {hearing_id} not found")

    comments = hearing.comments
    comment_dicts = [{"id": c.id, "body": c.body} for c in comments]

    clusters_data = cluster_comments(comment_dicts)

    try:
        # NULL out cluster_id on comments FIRST before deleting clusters
        db.session.execute(
            sa.update(PublicComment)
            .where(PublicComment.hearing_id == hearing_id)
            .values(cluster_id=None)
        )
        db.session.flush()

        # Now safe to delete clusters
        db.session.execute(
            sa.delete(CommentCluster).where(CommentCluster.hearing_id == hearing_id)
        )
        db.session.flush()

        saved_clusters = []
        comment_index = {c.id: c for c in comments}

        for cluster_data in clusters_data:
            cluster = CommentCluster(
                hearing_id=hearing_id,
                name=cluster_data["name"],
                description=cluster_data["description"],
            )
            db.session.add(cluster)
            db.session.flush()

            for cid in cluster_data["comment_ids"]:
                comment_index[cid].cluster_id = cluster.id

            saved_clusters.append(cluster)

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return saved_clusters