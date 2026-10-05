import unittest
from unittest import mock

import eia


class TestFetchSeries(unittest.TestCase):
    def test_pages_until_all_rows_are_fetched(self):
        # Pretend EIA has 7,000 rows: page 1 returns 5,000, page 2 returns 2,000
        page1 = {"total": "7000", "data": [{"period": "2020-01-01", "value": "1.5"}] * 5000}
        page2 = {"total": "7000", "data": [{"period": "2020-01-02", "value": "2.5"}] * 2000}
        with mock.patch.object(eia, "get", side_effect=[page1, page2]) as fake_get, \
             mock.patch.object(eia.time, "sleep"):
            df = eia.fetch_series("petroleum/pri/spt", "RWTC", "daily")
        self.assertEqual(fake_get.call_count, 2)
        self.assertEqual(fake_get.call_args_list[1].args[1]["offset"], 5000)
        self.assertEqual(len(df), 7000)

    def test_text_values_become_numbers_and_blanks_are_dropped(self):
        page = {"total": "3", "data": [
            {"period": "2020-04-20", "value": "-36.98"},  # real negative WTI price
            {"period": "2020-04-21", "value": None},
            {"period": "2020-04-22", "value": "13.78"},
        ]}
        with mock.patch.object(eia, "get", return_value=page):
            df = eia.fetch_series("petroleum/pri/spt", "RWTC", "daily")
        self.assertEqual(list(df["value"]), [-36.98, 13.78])


if __name__ == "__main__":
    unittest.main()
