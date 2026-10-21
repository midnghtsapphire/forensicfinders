import json, unittest
from pathlib import Path
from public_records_engine import PublicRecordsDataEngine, census_connector, SECTIONS

class T(unittest.TestCase):
    def eng(self): return PublicRecordsDataEngine(clock=lambda: "T0")
    def test_no_connectors_means_no_data_everywhere(self):
        r = self.eng().compile_all({"address": "x"})
        self.assertEqual({v["status"] for v in r["sections"].values()}, {"no_data"})
        self.assertEqual(set(r["sections"]), set(SECTIONS))
    def test_authority_required(self):
        with self.assertRaises(ValueError): self.eng().register("voter_records", lambda s: {}, authority=" ")
    def test_unknown_section(self):
        with self.assertRaises(ValueError): self.eng().register("bogus", lambda s: {}, authority="a")
    def test_connector_data_and_errors(self):
        e = self.eng().register("voter_records", lambda s: {"status": "ACTIVE"}, authority="MOU-1")
        e.register("vital_statistics", lambda s: 1 / 0, authority="MOU-2")
        r = e.compile_all({})["sections"]
        self.assertEqual(r["voter_records"], {"status": "ok", "authority": "MOU-1", "data": {"status": "ACTIVE"}})
        self.assertEqual(r["vital_statistics"]["status"], "error")
    def test_census_connector_uses_fixture(self):
        import os, sys
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "opendata"))
        from _fakenet import FakeOpener, fixture_json
        op = FakeOpener().add("GET", "https://geocoding.geo.census.gov/geocoder/geographies/onelineaddress",
                              (200, fixture_json("census_onelineaddress.json")))
        r = census_connector(opener=op)({"address": "1600 Pennsylvania Ave NW, Washington, DC 20500"})
        self.assertTrue(r)
    def test_census_connector_without_address(self):
        self.assertIsNone(census_connector()({}))

if __name__ == "__main__": unittest.main()
