from collections import OrderedDict
from bs4 import BeautifulSoup

# TODO
# * Find table by ID
# * Multi column headers
# * Multi row headers

from prettytable import PrettyTable
import pytest


class TableRow(object):
    def __init__(self, headers, row):
        self.row = OrderedDict(zip(headers, row))

    def __getitem__(self, item):
        return self.row[item]

    def __contains__(self, header):
        return header in self.row

    def values(self):
        return self.row.values()


class Table(object):
    def _insert_unique(self, header, result):
        header_to_insert = header
        header_number = 2
        while header_to_insert in result:
            header_to_insert = header + ' %s' % (header_number)
            header_number += 1
        result.append(header_to_insert)

    def _make_unique(self, headers):
        result = []
        for header in headers:
            self._insert_unique(header, result)
        return result

    def __init__(self, headers, rows=[]):
        self.headers = self._make_unique(headers)
        self.rows = [TableRow(self.headers, row) for row in rows]

    def __getitem__(self, item):
        return self.rows[item]

    def __str__(self):
        table = PrettyTable(self.headers)
        for row in self.rows:
            table.add_row(row.values())

        return '\n' + str(table)

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return str(self) == str(other)

    def __contains__(self, header):
        return header in self.headers

    def diff_str(self, other):
        from difflib import Differ
        d = Differ()
        return '\n'.join(d.compare(str(self).split('\n'), str(other).split('\n')))

    def get_column(self, header):
        return self.get_columns([header])

    def get_columns(self, headers):
        """Return new table containing only the columns specified by headers"""
        rows = ((row[header] for header in headers if header in row) for row in self.rows)
        return Table(headers, rows)

    def get_row(self, row_number):
        return self.get_rows(row_number, row_number + 1)

    def get_rows(self, from_row=0, to_row=0):
        """Return new table containing only the rows such that from_row<=row<to_row"""
        return Table(self.headers, (row.values() for row in self.rows[from_row:to_row]))

def parse_table(html):
    soup = BeautifulSoup(html)
    tables = soup.find_all('table')
    assert len(tables) > 0

    headers = []
    rows = []
    for row in tables[0].find_all('tr'):
        if not headers:
            headers = [c.get_text() for c in row.find_all('th')]
        else:
            rows.append([c.get_text() for c in row.find_all('td')])

    return Table(headers, rows)


def create_table(headers, rows=[]):
    return Table(headers, rows)

@pytest.fixture
def standard_table():
    return create_table(['Head 1', 'Head 2'],
                        [['Val 11', 'Val 12'],
                         ['Val 21', 'Val 22']])


def test_create_table_from_html_without_id(standard_table):
    html = """
    <table>
        <tr><th>Head 1</th><th>Head 2</th></tr>
        <tr><td>Val 11</td><td>Val 12</td></tr>
        <tr><td>Val 21</td><td>Val 22</td></tr>
    </table>
    """

    table = parse_table(html)
    assert table == standard_table


def test_create_table_from_header_and_rows(standard_table):
    assert standard_table[0]['Head 1'] == 'Val 11'
    assert standard_table[0]['Head 2'] == 'Val 12'
    assert standard_table[1]['Head 1'] == 'Val 21'
    assert standard_table[1]['Head 2'] == 'Val 22'


def test_empty_table_to_string():
    table = create_table(['Head 1', 'Head 2'], [])

    string = """
+--------+--------+
| Head 1 | Head 2 |
+--------+--------+
+--------+--------+"""

    assert str(table) == string


def test_table_with_values_to_string(standard_table):
    string = """
+--------+--------+
| Head 1 | Head 2 |
+--------+--------+
| Val 11 | Val 12 |
| Val 21 | Val 22 |
+--------+--------+"""
    assert str(standard_table) == string


def test_table_equality(standard_table):
    equal_table = create_table(['Head 1', 'Head 2'],
                              [['Val 11', 'Val 12'],
                               ['Val 21', 'Val 22']])

    assert equal_table == standard_table


def test_table_inequality(standard_table):
    different_table = create_table(['Head 1', 'Head 2'],
                                  [['Val 11', 'Val 12']])

    assert different_table != standard_table


def test_difference_empty_tables():
    # Not checking a whole lot in this tests, rather just executing the code
    table_a = create_table(["Head 1", "Head 2"])
    table_b = create_table(["Head 1", "Head 3"])

    assert len(table_a.diff_str(table_b)) > len(str(table_a))


def test_difference_table(standard_table):
    # Not checking a whole lot in this tests, rather just executing the code
    another_table = create_table(['Head 1', 'Head 2'],
                                [['Val 11', 'Val 12'],
                                 ['Val 31', 'Val 22']])

    assert len(standard_table.diff_str(another_table)) > len(str(another_table))


def test_get_all_columns_in_table(standard_table):
    assert standard_table.get_columns(['Head 1', 'Head 2']) == standard_table


def test_get_subset_of_all_columns_in_table(standard_table):
    expected_table = create_table(['Head 1'],
                                 [['Val 11'],
                                  ['Val 21']])

    assert standard_table.get_column('Head 1') == expected_table


def test_get_subset_of_all_rows_in_table(standard_table):
    expected_table = create_table(['Head 1', 'Head 2'],
                                 [['Val 21', 'Val 22']])

    assert standard_table.get_rows(1, 2) == expected_table, expected_table.diff_str(standard_table)
    assert standard_table.get_row(1) == expected_table, expected_table.diff_str(standard_table)


def test_contains_column(standard_table):
    assert 'Head 1' in standard_table
    assert 'Head 3' not in standard_table


def test_table_with_non_unique_table_headers():
    table = create_table(['Head 1', 'Head 2',  'Head 2', 'Head 2'],
                        [['Val 21', 'Val 221', 'Val 222',  'Val 223']])

    expected_table = create_table(['Head 1', 'Head 2',  'Head 2 2', 'Head 2 3'],
                                 [['Val 21', 'Val 221', 'Val 222',  'Val 223']])

    assert table == expected_table