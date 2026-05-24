from inspect import signature
from unittest import TestCase

from pyaarlo import PyArlo


class FakeBackend(object):
    def __init__(self, response):
        self.response = response
        self.posts = []

    def post(self, path, params):
        self.posts.append((path, params))
        return self.response


class TestFeedMetadata(TestCase):
    def test_feed_metadata_posts_request_and_returns_response(self):
        response = {
            "groupByEvents": {
                "event-key": [
                    {
                        "device-key": [
                            {
                                "feedId": "feed-id",
                                "name": "video-id",
                                "deviceId": "device-id",
                                "harlem": [
                                    {
                                        "shortCaption": "Animal crosses yard",
                                        "aiDigest": [
                                            {
                                                "sectionName": "Generic Description",
                                                "content": "Animal crosses yard.",
                                            }
                                        ],
                                        "highlight": False,
                                        "modelName": "gemini",
                                    }
                                ],
                            }
                        ]
                    }
                ]
            },
            "nextPage": "next-page",
        }
        backend = FakeBackend(response)
        arlo = PyArlo.__new__(PyArlo)
        arlo._be = backend

        metadata = arlo.feed_metadata(
            "owner-id",
            "location-id",
            "20260524",
            limit=25,
            group_by="type",
            next_page="previous-page",
            asc=True,
        )

        self.assertIs(metadata, response)
        self.assertEqual(
            backend.posts,
            [
                (
                    "/hmsfeeds/users/owner-id/location-id/metadata",
                    {
                        "asc": True,
                        "fromDate": "20260524",
                        "limit": 25,
                        "groupBy": "type",
                        "nextPage": "previous-page",
                    },
                )
            ],
        )

    def test_feed_metadata_uses_feed_defaults(self):
        backend = FakeBackend({})
        arlo = PyArlo.__new__(PyArlo)
        arlo._be = backend

        arlo.feed_metadata("owner-id", "location-id", "20260524")

        self.assertEqual(
            backend.posts[0],
            (
                "/hmsfeeds/users/owner-id/location-id/metadata",
                {
                    "asc": False,
                    "fromDate": "20260524",
                    "limit": 200,
                    "groupBy": "events",
                    "nextPage": None,
                },
            ),
        )

    def test_feed_items_flattens_group_by_events(self):
        harlem = [
            {
                "shortCaption": "Animal crosses yard",
                "modelName": "gemini",
            }
        ]
        first_item = {
            "feedId": "feed-id-1",
            "name": "video-id-1",
            "deviceId": "device-id-1",
            "harlem": harlem,
        }
        second_item = {
            "feedId": "feed-id-2",
            "name": "video-id-2",
            "deviceId": "device-id-2",
        }
        third_item = {
            "feedId": "feed-id-3",
            "name": "video-id-3",
            "deviceId": "device-id-3",
        }
        response = {
            "groupByEvents": {
                "event-key-1": [
                    {
                        "device-key-1": [
                            first_item,
                            second_item,
                        ],
                        "device-key-2": [
                            third_item,
                        ],
                    }
                ],
            },
            "nextPage": "next-page",
        }
        backend = FakeBackend(response)
        arlo = PyArlo.__new__(PyArlo)
        arlo._be = backend

        items = arlo.feed_items(
            "owner-id",
            "location-id",
            "20260524",
            limit=25,
            next_page="previous-page",
        )

        self.assertEqual(items, [first_item, second_item, third_item])
        self.assertIs(items[0], first_item)
        self.assertIs(items[1], second_item)
        self.assertIs(items[2], third_item)
        self.assertIs(items[0]["harlem"], harlem)
        self.assertEqual(
            backend.posts,
            [
                (
                    "/hmsfeeds/users/owner-id/location-id/metadata",
                    {
                        "asc": False,
                        "fromDate": "20260524",
                        "limit": 25,
                        "groupBy": "events",
                        "nextPage": "previous-page",
                    },
                )
            ],
        )

    def test_feed_items_always_requests_event_grouping(self):
        self.assertNotIn("group_by", signature(PyArlo.feed_items).parameters)

        backend = FakeBackend({})
        arlo = PyArlo.__new__(PyArlo)
        arlo._be = backend

        arlo.feed_items("owner-id", "location-id", "20260524")

        self.assertEqual(backend.posts[0][1]["groupBy"], "events")

    def test_feed_items_returns_empty_list_for_unexpected_metadata(self):
        arlo = PyArlo.__new__(PyArlo)

        self.assertEqual(arlo._feed_items_from_metadata(None), [])
        self.assertEqual(arlo._feed_items_from_metadata({}), [])
        self.assertEqual(arlo._feed_items_from_metadata({"groupByEvents": []}), [])
