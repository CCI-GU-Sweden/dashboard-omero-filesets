from datetime import date
from unittest import TestCase
from unittest.mock import patch

from omero_filesets import data


class OverviewTests(TestCase):
    @patch('omero_filesets.data.connection')
    def test_researcher_groups_restrict_both_snapshots_and_omit_billing(self, connection):
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [
            ('current', date(2026, 11, 8), 4, 2),
            ('previous', date(2026, 10, 9), 2, 1),
        ]
        result = data.overview_card(allowed_group=[42])
        sql, params = cursor.execute.call_args.args
        self.assertIn('group_id = ANY(%s)', sql)
        self.assertEqual(params, [[42]])
        self.assertNotIn('daily_charge_ore', sql)
        self.assertNotIn('daily_sek', result['metrics'])
        self.assertEqual(result['metrics']['filesets']['change_percent'], 100.0)

    @patch('omero_filesets.data.connection')
    def test_empty_snapshot_is_not_reported_as_zero(self, connection):
        connection.cursor.return_value.__enter__.return_value.fetchall.return_value = []
        result = data.overview_card()
        self.assertIsNone(result['snapshot_date'])
        self.assertIsNone(result['metrics']['filesets']['value'])
