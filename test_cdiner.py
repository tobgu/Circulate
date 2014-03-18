
def print_relations(relations, dimension_size):
    for x in range(0, dimension_size*dimension_size, dimension_size):
        print relations[x:x+dimension_size]

if __name__ == '__main__':
    from dinerc import calc_tables, calc_conference
    weight_matrix = [[1, 2, 3, 3],
                     [4, 5, 6, 7],
                     [7, 8, 9, 10],
                     [17, 18, 19, 11]]
#    print calc_tables(1.0, weight_matrix, [1, 2, 3, 4], [3, 1])

    participants = [[0, 1, 2], [1, 2, 3]]
    tables = [[1, 2], [2, 1]]
    score, participants, relations = calc_conference(1.0, 5, weight_matrix, participants, tables)
    print "Calc conference: %s, %s" % (score, participants)
    print_relations(relations, len(weight_matrix))