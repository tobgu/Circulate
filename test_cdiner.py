from dinerc import calc_tables, calc_conference
from xlsm_io import conference_data


def print_relations(relations, dimension_size):
    for x in range(0, dimension_size*dimension_size, dimension_size):
        print relations[x:x+dimension_size]

def small_test():
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


def group_seatings(conference, participants):
    conference['placements'] = {}
    for i, (name, table_sizes) in enumerate(zip(conference['seating_names'], conference['table_sizes'])):
        start = 0
        participants_by_table = []
        for size in table_sizes:
            participants_by_table.append([conference['staff_names'][p] for p in participants[i][start:start+size]])
            start += size

        conference['placements'][name] = participants_by_table


def print_seatings(conference):
    for name, tables in conference['placements'].items():
        print (u"\n%s" % name).encode('utf-8')
        print "--------------------------------"
        for i, table in enumerate(tables):
            print "\nTable %s" % (i+1)
            for participant in table:
                print participant.encode('utf-8')


def large_test():
    print "Reading conference data"
    conference = conference_data()
    print "Done"
    score, participants, relations = calc_conference(1.0, 5, conference['weight_matrix'],
                                                     conference['guests'], conference['table_sizes'])
    print "Calc conference: %s, %s" % (score, participants)

    group_seatings(conference, participants)
    print_seatings(conference)

if __name__ == '__main__':
    large_test()