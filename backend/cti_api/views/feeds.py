from cti_api.db.mongo import source_feeds
from cti_api.serializers import SourceFeedSerializer
from cti_api.views.mongo_crud import make_mongo_views

FeedListView, FeedDetailView = make_mongo_views(
    source_feeds,
    SourceFeedSerializer,
    "feed_id",
)
