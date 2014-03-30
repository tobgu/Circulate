from collections import OrderedDict
from dinerc import calc_tables, calc_conference
from xlsm_io import read_conference_data, write_seating


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


def print_seatings(conference):
    for name, tables in conference['placements'].items():
        print (u"\n%s" % name).encode('utf-8')
        print "--------------------------------"
        for i, table in enumerate(tables):
            print "\nTable %s" % (i+1)
            for participant in table:
                print participant.encode('utf-8')


# TODO
# x - Write to excel
# - Measure time taken to loop and merge some of the loops
# - Get the web interface working including subprocessing
# - Measure the read in times and improve them if possible
# - Make some sort of validation of the generated data, writing down weights and reoccuring pairs?
# - Make it possible to start from a fixed position
# - Make it possible to lock certain individuals to certain positions and optimize from there
# - Dust of the table based algorithm to make it work over the whole conference
# - Print tables and participants ordered by the last or first name of the participant

def large_test():
    print "Reading conference data"
    conference = read_conference_data()
    print "Done"
    score, participants, relations = calc_conference(1.0, 5, conference['weight_matrix'],
                                                     conference['guests'], conference['table_sizes'])
    print "Calc conference: %s, %s" % (score, participants)

    group_seatings(conference, participants)
#    print_seatings(conference)
    write_seating(conference)

if __name__ == '__main__':
    large_test()