import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from webui.server.agent_runtime.service import AssistantService


class TestAssistantServiceStreamDelta(unittest.TestCase):
    def setUp(self):
        self.tempdir = TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.service = AssistantService(project_root=Path(self.tempdir.name))

    def test_extract_text_delta_from_partial_event(self):
        message = SimpleNamespace(
            event={
                "type": "content_block_delta",
                "delta": {"type": "text_delta", "text": "你好"},
            }
        )
        self.assertEqual(self.service._extract_partial_delta(message), "你好")

    def test_extract_text_from_content_block_start(self):
        message = SimpleNamespace(
            event={
                "type": "content_block_start",
                "content_block": {"type": "text", "text": "开头"},
            }
        )
        self.assertEqual(self.service._extract_partial_delta(message), "开头")

    def test_split_text_chunks(self):
        chunks = self.service._split_text_chunks("abcdefghij", chunk_size=4)
        self.assertEqual(chunks, ["abcd", "efgh", "ij"])


if __name__ == "__main__":
    unittest.main()
