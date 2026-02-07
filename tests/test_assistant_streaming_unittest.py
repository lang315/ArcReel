import unittest

from webui.server.agent_runtime.streaming import StreamRequestRegistry


class TestAssistantStreaming(unittest.IsolatedAsyncioTestCase):
    async def test_stream_event_sequence(self):
        registry = StreamRequestRegistry()
        stream_request = await registry.create_request(
            session_id="session_1",
            user_message_id=1,
        )

        await stream_request.emit("ack", {"session_id": "session_1"})
        await stream_request.emit("delta", {"text": "hello"})
        await stream_request.emit("done", {"assistant_message_id": 2})

        first = await stream_request.next_event()
        second = await stream_request.next_event()
        third = await stream_request.next_event()

        self.assertEqual(first.id, 1)
        self.assertEqual(first.event, "ack")
        self.assertEqual(second.id, 2)
        self.assertEqual(second.data["text"], "hello")
        self.assertEqual(third.id, 3)
        self.assertEqual(third.event, "done")
        self.assertTrue(stream_request.closed)

        await registry.remove_request("session_1", stream_request.request_id)
        missing = await registry.get_request("session_1", stream_request.request_id)
        self.assertIsNone(missing)

    def test_ping_event_payload(self):
        payload = StreamRequestRegistry.ping_event()
        self.assertIn("event: ping", payload)
        self.assertIn("data:", payload)


if __name__ == "__main__":
    unittest.main()
