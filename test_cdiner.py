from dinerc import calc_conference
from diner import add_seatings, create_relation_list, calc_conference_wrapper
from xlsm_io import read_conference_data
from time import time

def print_relations(relations, dimension_size):
    for x in range(0, dimension_size*dimension_size, dimension_size):
        print relations[x:x+dimension_size]


def small_test():
    conference = {}
    conference['weight_matrix'] = [[1, 2, 3, 3],
                                   [4, 5, 6, 7],
                                   [7, 8, 9, 10],
                                   [17, 18, 19, 11]]

    conference['guests'] = [[{'id': 0, 'fix': False}, {'id': 1, 'fix': False}, {'id': 2, 'fix': False}],
                            [{'id': 1, 'fix': False}, {'id': 2, 'fix': False}, {'id': 3, 'fix': False}]]
    conference['table_sizes'] = [[1, 2], [2, 1]]

    result = calc_conference_wrapper((1.0, conference, 1))

    # This is the expected result when no participants have been fixed
    assert result['participants'][0][0]['id'] == 2

    # Fix participant 0 and rerun the test
    conference['guests'][0][0]['fix'] = True
    result = calc_conference_wrapper((1.0, conference, 1))
    assert result['participants'][0][0]['id'] == 0

    # Now fix participant 2 and rerun the test
    conference['guests'][0][0]['fix'] = False
    conference['guests'][0][2]['fix'] = True

    # This time a switch is performed but it is less optimal than if we could choose freely
    result = calc_conference_wrapper((1.0, conference, 1))
    assert result['participants'][0][0]['id'] == 1
    assert not result['participants'][0][0]['fix']
    assert result['participants'][0][2]['fix']


    score = result['score']
    participants = result['participants']
    relations = result['relations']

    print "Calc conference: %s, %s" % (score, participants)
    print_relations(relations, len(conference['weight_matrix']))


def print_seatings(conference):
    for name, tables in conference['placements'].items():
        print (u"\n%s" % name).encode('utf-8')
        print "--------------------------------"
        for i, table in enumerate(tables):
            print "\nTable %s" % (i+1)
            for participant in table:
                print participant.encode('utf-8')


def large_test():
    start = time()
    print "Reading conference data"
    conference = read_conference_data()
    conference_read = time()
    print "Done, time=%s" % (conference_read - start)


    result = calc_conference_wrapper((1.0, conference, 1))

    score = result['score']
    tests_count = result['test_count']
    scramble_count = result['scramble_count']
    participants = result['participants']
    relations = result['relations']

    conference_optimized = time()
    print "Calc conference: time=%s, score=%s, tests_count=%s, scramble_count=%s, participants=%s" % (conference_optimized - conference_read,
                                                                                   score,
                                                                                   tests_count,
                                                                                   scramble_count,
                                                                                   participants)

    add_seatings(conference, participants)
    seatings_grouped = time()
    print "Seatings grouped %s" % (seatings_grouped - conference_optimized)

#    write_seating(conference)
    print "Conference written %s" % (time() - seatings_grouped)

    create_relation_list(relations, conference)


if __name__ == '__main__':
    large_test()
    small_test()