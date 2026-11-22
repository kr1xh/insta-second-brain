import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import sweep  # noqa: E402


def edge(cid, name, count):
    return {"node": {"collection_id": cid, "collection_name": name, "collection_media_count": count}, "cursor": "c"}


def test_counts_from_current_viewer_shape():
    payload = {"data": {"viewer": {"collections_unified_with_auto_collections": {
        "edges": [edge("1", "Cold email", 34), edge("2", "Hooks", 120)]}}}}
    assert sweep.parse_collection_counts(payload) == [
        {"id": "1", "name": "Cold email", "posts": 34}, {"id": "2", "name": "Hooks", "posts": 120}]


def test_counts_from_older_shape():
    payload = {"data": {"xdt_api__v1__collections__list_graphql_connection": {"edges": [edge("9", "Old", 3)]}}}
    assert sweep.parse_collection_counts(payload) == [{"id": "9", "name": "Old", "posts": 3}]


def test_counts_ignore_unrelated_payloads_and_nodes_without_id():
    assert sweep.parse_collection_counts({"data": {"user": {}}}) == []
    assert sweep.parse_collection_counts({"data": {"viewer": {"collections_unified_with_auto_collections": {
        "edges": [{"node": {"collection_name": "x"}}]}}}}) == []
