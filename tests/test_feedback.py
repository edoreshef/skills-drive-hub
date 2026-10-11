"""feedback.py writes one file only with consent; collect-feedback.py adds each file once."""

import csv
import unittest

from helpers import MAINTAINER, ToolTest, read_json, run, tool

FEEDBACK = tool("feedback")
COLLECT = MAINTAINER / "collect-feedback.py"


class FeedbackTest(ToolTest):
    def feedback(self, *extra, package="domain-sample", skill="block-notes", worked="yes", version="0.1.0"):
        return run(FEEDBACK, "--dest", self.tmp / "feedback", "--package", package, "--skill", skill,
                   "--author", "other@example.com", "--question", "Did it work?", "--worked", worked,
                   "--version", version, *extra)

    def collect(self):
        return run(COLLECT, "--feedback", self.tmp / "feedback", "--sheet", self.tmp / "sheet.csv")

    def rows(self):
        with (self.tmp / "sheet.csv").open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def test_feedback_needs_consent_and_collects_once(self):
        refused = self.feedback(worked="no")
        self.assertEqual(refused.returncode, 1, refused.stdout)
        self.assertIn("consent required", refused.stderr)
        self.assertFalse((self.tmp / "feedback").exists())

        wrote = self.feedback("--note", "Row matched.", "--consent")
        self.assertEqual(wrote.returncode, 0, wrote.stderr)
        files = list((self.tmp / "feedback").glob("*.json"))
        self.assertEqual(len(files), 1)
        self.assertTrue(files[0].name.endswith("__other__block-notes.json"))
        payload = read_json(files[0])
        self.assertIs(payload["worked"], True)
        self.assertEqual(payload["package"], "domain-sample")

        self.assertIn("added 1", self.collect().stdout)
        self.assertIn("added 0", self.collect().stdout)
        rows = self.rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0]["skill"], rows[0]["worked"], rows[0]["note"]), ("block-notes", "yes", "Row matched."))

        self.feedback("--consent", package="foundation-sample", skill="shared-terms", worked="no", version="0.2.0")
        self.assertIn("added 1", self.collect().stdout)
        rows = self.rows()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1]["worked"], "no")


if __name__ == "__main__":
    unittest.main()
