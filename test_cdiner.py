from dinerc import calc_occasion, calc_conference
import itertools
from diner import add_seatings, create_relation_list
from xlsm_io import read_conference_data, write_seating
from time import time

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
# x - Get the web interface working including subprocessing
# - ~ Measure the read in times and improve them if possible
# - Make some sort of validation of the generated data, writing down weights and reoccuring pairs?
# - Make it possible to start from a fixed position
# - Make it possible to lock certain individuals to certain positions and optimize from there
# - Dust of the table based algorithm to make it work over the whole conference
# - Print tables and participants ordered by the last or first name of the participant
# - Some sort if drag and drop HTML interface as a complement to the excel file delivered
#   for intermediate seating manipulation

def large_test(conference):
    start = time()
    score, tests_count, scramble_count, participants, relations = calc_conference(1.0, conference['weight_matrix'],
                                                                  conference['guests'], conference['table_sizes'], 1)
    conference_optimized = time()
    print "Calc conference: time=%s, score=%s, tests_count=%s, scramble_count=%s, participants=%s" % (conference_optimized - start,
                                                                                   score,
                                                                                   tests_count,
                                                                                   scramble_count,
                                                                                   participants)

    add_seatings(conference, participants)
    seatings_grouped = time()
    print "Seatings grouped %s" % (seatings_grouped - conference_optimized)

    write_seating(conference)
    print "Conference written %s" % (time() - seatings_grouped)

    create_relation_list(relations, conference)


def large_linear_test(conference):
    occasion_count = len(conference['seating_names'])

    placements = []
    relation_matrices = []
    for i in range(occasion_count):
        iterations, score, tests_count, seatings, relations = calc_occasion(0.5,
                                                  conference['weight_matrix'],
                                                  conference['guests'][i],
                                                  conference['table_sizes'][i])
        placements.append(seatings)
        relation_matrices.append(relations)
        print "iterations: %s, score: %s, tests_count: %s, seatings: %s, relations: %s" % (iterations,
                                                                            score,
                                                                            tests_count,
                                                                            seatings,
                                                                            len(relations))

    add_seatings(conference, placements)
    total_relations = [sum(r) for r in zip(*relation_matrices)]

    # The same calculation that is done in the C code for the global optimization
    score = sum((w + 1) * (2 ** (r - 1)) if r > 0 else 0 for w, r in zip(itertools.chain(*conference['weight_matrix']), total_relations))
    print create_relation_list(total_relations, conference)
    print "Total score: %s" % score


if __name__ == '__main__':
    start = time()
    print "Reading conference data"
    conference = read_conference_data()
    conference_read = time()
    print "Done, time=%s" % (conference_read - start)

    large_test(conference)
#    large_linear_test(conference)