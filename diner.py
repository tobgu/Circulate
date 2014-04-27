import multiprocessing
from time import time
import itertools
from xlsm_io import read_conference_data, write_seating, add_global_simulation_info
from dinerc import calc_conference

CLIMB_MODE_ALWAYS = 1
CLIMB_MODE_NEVER = 2


def add_seatings(conference, participants):
    conference['placements'] = []
    for i, (name, table_sizes) in enumerate(zip(conference['seating_names'], conference['table_sizes'])):
        start = 0
        participants_by_table = []
        for size in table_sizes:
            participants_by_table.append(participants[i][start:start+size])
            start += size

        conference['placements'].append({'name': name, 'tables': participants_by_table})


def guest_properties(guests_per_occasion, property_name):
    return [[g[property_name] for g in occasion] for occasion in guests_per_occasion]


def calc_conference_wrapper(args):
    simulation_time, conference, climb_mode = args
#    print conference['guests']
    guest_ids = guest_properties(conference['guests'], 'id')
    guest_fix_indicators = [[1 if fixed else 0 for fixed in occasion] for occasion in guest_properties(conference['guests'], 'fix')]
    print guest_fix_indicators

    score, test_count, scramble_count, participants, relations = calc_conference(simulation_time,
                                                                                 conference['weight_matrix'],
                                                                                 guest_ids,
                                                                                 guest_fix_indicators,
                                                                                 conference['table_sizes'],
                                                                                 climb_mode)

    # Should be safe to set the fix indicators based on what is in the input since the fixed
    # participants don't move.
    participants = [[{'id': id, 'fix': participant['fix']} for id, participant in zip(result_occasion, input_occasion)]
                    for result_occasion, input_occasion in zip(participants, conference['guests'])]

    return {'score': score, 'test_count': test_count, 'scramble_count': scramble_count,
            'participants': participants, 'relations': relations}


def chunks(l, n):
    for i in xrange(0, len(l), n):
        yield l[i:i+n]


# table_sizes: list of list with sizes for each occasion
def seatings_to_guest_list(seatings):
    table_sizes = []
    seating_names = []
    guests = []
    for seating in seatings:
        table_sizes.append([len(t) for t in seating['tables']])
        seating_names.append(seating['name'])
        guests.append(list(itertools.chain(*seating['tables'])))

    return guests, table_sizes, seating_names


def create_relation_list(relations, conference):
    result = []

    # relations is a straight list, chunk it down to a matrix like list of lists
    for i, rel in enumerate(chunks(relations, len(conference['weight_matrix']))):
        for j, count in enumerate(rel[:i]):
            if count > 0:
                result.append((i, j, count, conference['weight_matrix'][i][j]))

    # Sort on times seated at the same table and badness
    return sorted(result, key=lambda x: (x[2], x[3]), reverse=True)


def do_run_global_simulation(climb_mode, conference, simulation_time):
    pool_size = multiprocessing.cpu_count()
    pool = multiprocessing.Pool(processes=pool_size)
    start = time()
    results = pool.map(calc_conference_wrapper, pool_size * [[simulation_time, conference, climb_mode]])
    duration = time() - start
    pool.close()
    pool.join()
    best_result = min(results, key=lambda r: r['score'])
    test_count = sum(r['test_count'] for r in results)
    scramble_count = sum(r['scramble_count'] for r in results)
    relation_list = create_relation_list(best_result['relations'], conference)
    return best_result, duration, relation_list, scramble_count, test_count


def run_simulation(conference, simulation_time, climb_mode):
    best_result, duration, relation_list, scramble_count, tests_count = \
        do_run_global_simulation(climb_mode, conference, simulation_time)

    add_seatings(conference, best_result['participants'])

    return {'conference': conference,
            'score': best_result['score'],
            'total_tests_count': tests_count,
            'total_iteration_count': scramble_count,
            'duration': duration,
            'relations': relation_list}

        # TODO:
        # - Would be nice to be able to select
        #   * No optimization, only scrambling
        #   * Optimization on every scramble
        #   * Optimization on best scramble
        # - Some way of specifying a multiplication factor for the relations to push
        #   persons away from each other?
        # - Add a pivot table showing the number of relations by times they were seated
        #   together (their score in the relation matrix, right now the number of times
        #   seated).
        # - Add a list of all participant sorted by name per event with the table number
        #   after.
        # - Try to increase the penalty for sitting next to each other multiple times
        # - Show if constalations of persons have been sitting next to each other at
        #   multiple occasions (rings of people...)
