import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from webui.server.agent_runtime.session_store import AgentSessionStore


class TestAgentSessionStore(unittest.TestCase):
    def test_session_lifecycle(self):
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / ".agent_sessions.db"
            store = AgentSessionStore(db_path)

            session = store.create_session(project_name="demo", title="Demo Session")
            self.assertEqual(session.project_name, "demo")
            self.assertEqual(session.status, "active")

            sessions = store.list_sessions(project_name="demo")
            self.assertEqual(len(sessions), 1)
            self.assertEqual(sessions[0].id, session.id)

            user_message = store.add_message(
                session_id=session.id,
                role="user",
                content="hello",
            )
            assistant_message = store.add_message(
                session_id=session.id,
                role="assistant",
                content="world",
            )

            self.assertGreater(user_message.id, 0)
            self.assertGreater(assistant_message.id, user_message.id)

            messages = store.list_messages(session.id)
            self.assertEqual(len(messages), 2)
            self.assertEqual(messages[0].role, "user")
            self.assertEqual(messages[1].role, "assistant")

            archived = store.archive_session(session.id)
            self.assertTrue(archived)

            archived_session = store.get_session(session.id)
            self.assertIsNotNone(archived_session)
            self.assertEqual(archived_session.status, "archived")

            updated = store.update_session_title(session.id, "Renamed Session")
            self.assertTrue(updated)
            renamed_session = store.get_session(session.id)
            self.assertIsNotNone(renamed_session)
            self.assertEqual(renamed_session.title, "Renamed Session")

            deleted = store.delete_session(session.id)
            self.assertTrue(deleted)
            self.assertIsNone(store.get_session(session.id))

    def test_add_message_invalid_session(self):
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / ".agent_sessions.db"
            store = AgentSessionStore(db_path)

            with self.assertRaises(ValueError):
                store.add_message(
                    session_id="missing",
                    role="user",
                    content="hello",
                )


if __name__ == "__main__":
    unittest.main()
