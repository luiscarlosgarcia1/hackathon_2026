from app import db
from app.models.comment_cluster import CommentCluster
from app.models.public_comment import PublicComment
from app.services.clustering_service import cluster_comments
from app.services.hearing_service import get_hearing


def run_clustering(hearing_id: int) -> list[CommentCluster]:
    hearing = get_hearing(hearing_id)
    if hearing is None:
        raise LookupError(f"hearing {hearing_id} not found")

    comments = hearing.comments
    comment_dicts = [{"id": c.id, "body": c.body} for c in comments]

    # raises ValueError if < 2 comments — let caller handle
    clusters_data = cluster_comments(comment_dicts)

    try:
        # Full replace: delete existing clusters for this hearing
        CommentCluster.query.filter_by(hearing_id=hearing_id).delete()

        # Null out cluster_id on all comments so FK constraint is satisfied
        for comment in comments:
            comment.cluster_id = None
        db.session.flush()

        # Insert new clusters and assign comments
        saved_clusters = []
        comment_index = {c.id: c for c in comments}

        for cluster_data in clusters_data:
            cluster = CommentCluster(
                hearing_id=hearing_id,
                name=cluster_data["name"],
                description=cluster_data["description"],
            )
            db.session.add(cluster)
            db.session.flush()  # get cluster.id

            for cid in cluster_data["comment_ids"]:
                comment_index[cid].cluster_id = cluster.id

            saved_clusters.append(cluster)

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return saved_clusters
