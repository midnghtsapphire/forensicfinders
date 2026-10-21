import unittest, sources

class TestSources(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.d = sources.load()

    def test_structure(self):
        self.assertEqual(sources.validate(self.d), [])

    def test_every_cited_doi_is_in_table(self):
        m = sources.missing(self.d)
        self.assertEqual(m, {}, "DOIs cited in sar/ but missing from data/sources.json: %s" % m)

    def test_placeholders_not_rows(self):
        dois = set(sources.by_doi(self.d))
        for p in self.d["excluded_placeholder_dois"]: self.assertNotIn(p, dois)

    def test_doi_regex_keeps_parentheses(self):
        self.assertEqual(sources.DOI_RE.findall("doi:[10.1016/S0379-0738(01)00418-2](x)")[0], "10.1016/S0379-0738(01)00418-2")

    def test_known_caveats_recorded(self):
        notes = " ".join(r["notes"] for r in self.d["sources"])
        for k in ("Pringle", "PMC7732738", "urs.earthrs.gov", "Meet GEDI"): self.assertIn(k, notes)

    def test_rendered_md_is_current(self):
        self.assertEqual(sources.MD.read_text(), sources.render(self.d), "run: python3 sar/sources.py --render")

if __name__ == "__main__":
    unittest.main()
