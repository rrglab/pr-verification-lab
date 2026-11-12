"""Synthetic/public-only contract fixture for identity-addressed inbound delivery.

This is an independent toy model, NOT copied product source, and cannot
certify the behavior of a separate private pull request.
"""
import unittest


class ToyReceiver:
    """Minimal state machine for testing the public contract."""

    def __init__(self):
        self.actors = {"@person": "human-1", "@merchant": "merchant-1"}
        self.verified_endpoints = {"merchant-channel": "@merchant"}
        self.accepted = {}

    def bind_person_channel(self, channel):
        self.person_channel = channel

    def receive(self, *, trusted, endpoint, recipient, event_id, content):
        if trusted is not True:
            raise PermissionError("unverified channel")
        sender = self.verified_endpoints.get(endpoint)
        if sender is None or recipient not in self.actors:
            raise LookupError("unresolvable address or channel")
        if not event_id or not content:
            raise ValueError("required event fields")
        key = (endpoint, event_id)
        candidate = (sender, recipient, content)
        existing = self.accepted.get(key)
        if existing is not None and existing != candidate:
            raise ValueError("conflicting replay")
        self.accepted[key] = candidate
        return {"sender": sender, "recipient": recipient, "content": content,
                "effect_authorized": False}


class InboundContractFixture(unittest.TestCase):
    def setUp(self):
        self.receiver = ToyReceiver()
        self.message = {"trusted": True, "endpoint": "merchant-channel",
                        "recipient": "@person", "event_id": "evt-1",
                        "content": "Your case has been reviewed"}

    def test_one_address_survives_channel_replacement(self):
        identity = self.receiver.actors["@person"]
        self.receiver.bind_person_channel("phone-old")
        self.receiver.bind_person_channel("phone-new")
        self.assertEqual(self.receiver.actors["@person"], identity)
        self.assertEqual(self.receiver.receive(**self.message)["recipient"], "@person")

    def test_verified_business_origin_reaches_person(self):
        delivery = self.receiver.receive(**self.message)
        self.assertEqual(delivery["sender"], "@merchant")
        self.assertEqual(delivery["recipient"], "@person")
        self.assertFalse(delivery["effect_authorized"])

    def test_unverified_origin_is_denied(self):
        with self.assertRaises(PermissionError):
            self.receiver.receive(**{**self.message, "trusted": False})

    def test_unknown_channel_or_address_is_denied(self):
        for changed in ({"endpoint": "unregistered"}, {"recipient": "@nobody"}):
            with self.subTest(changed=changed), self.assertRaises(LookupError):
                self.receiver.receive(**{**self.message, **changed})

    def test_exact_retry_is_idempotent(self):
        self.assertEqual(self.receiver.receive(**self.message),
                         self.receiver.receive(**self.message))
        self.assertEqual(len(self.receiver.accepted), 1)

    def test_conflicting_replay_is_rejected(self):
        self.receiver.receive(**self.message)
        for changed in ({"content": "Authorize payment"},
                        {"recipient": "@merchant"}):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                self.receiver.receive(**{**self.message, **changed})

    def test_invalid_event_id_is_rejected(self):
        with self.assertRaises(ValueError):
            self.receiver.receive(**{**self.message, "event_id": ""})


if __name__ == "__main__":
    unittest.main()
