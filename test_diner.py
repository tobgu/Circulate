from diner import create_tables2, create_tables


def test_create_table_versions_basic():
    weights = [
        [0, 2, 5],
        [2, 0, 5],
        [5, 5, 0],
    ]

    participants = [0, 1, 2,]
    table_sizes = [3]
    assert create_tables2(participants, table_sizes, weights) == create_tables(participants, table_sizes, weights)


def test_create_table_versions_advanced():
    weights = [
        [0, 2, 5, 2, 1],
        [2, 0, 5, 7, 2],
        [5, 5, 0, 0, 4],
        [2, 7, 0, 0, 4],
        [1, 2, 4, 4, 0],
    ]

    participants = [0, 1, 2, 3, 4]
    table_sizes = [3, 2]
    tables = create_tables(participants, table_sizes, weights)
    tables2 = create_tables2(participants, table_sizes, weights)
    assert tables == tables2