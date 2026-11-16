"""Public index must disclose that machine checks differ from human clinical review."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PublicReviewLabelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.script = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")

    def test_published_bibliography_is_primary_page_section(self):
        self.assertLess(self.page.index('<section id="discovery"'),
                        self.page.index('<section id="evidence"'))
        self.assertIn('id="discovery-check"', self.page)
        self.assertIn('id="bibliography-check-status"', self.page)

    def test_review_labels_distinguish_metadata_and_human_checks(self):
        for status in ("Automated metadata check passed",
                       "Independently matched source identity",
                       "Human clinical review pending"):
            self.assertIn(status, self.script)
        self.assertIn("reviewLevel(r)", self.script)
        self.assertIn("verification_online_ledger.json", self.script)
        self.assertIn("verification_report.json", self.script)

    def test_api_failure_never_implies_approval(self):
        self.assertIn("Verification report unavailable or updating", self.script)
        self.assertIn("if (!auditReport) return 'pending'", self.script)
        self.assertIn("local_metadata_flagged === 0", self.script)

    def test_no_clinical_approval_claim(self):
        self.assertIn("Automated checks do not validate eligibility", self.script)
        self.assertIn("not clinical guidance", self.page)


if __name__ == "__main__":
    unittest.main()
