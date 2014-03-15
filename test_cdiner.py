if __name__ == '__main__':
    from dinerc import calc_tables, calc_conference
    weight_matrix = [[1, 2, 3, 3], [4, 5, 6, 7], [7, 8, 9, 10], [17, 18, 19, 11]]
#    print calc_tables(1.0, weight_matrix, [1, 2, 3, 4], [3, 1])

    participants = [[1, 2, 3], [2, 3, 4]]
    tables = [[1, 2], [2, 1]]
    print "Calc conference: %s" % calc_conference(1.0, 5, weight_matrix, participants, tables)