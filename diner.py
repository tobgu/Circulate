from collections import OrderedDict
from random import random, sample
import multiprocessing
from time import time
import itertools
from xlsm_io import read_conference_data, write_seating, add_global_simulation_info, write_score
from dinerc import calc_occasion, calc_conference


def calc_weight_matrix():
    eater_count = 200
    eaters = ['eater %s' % i for i in range(eater_count)]
    group_weights = [2, 1, 5, 2, 3, 1, 10, 2, 4, 7]
    group_participation = [[w if random() < 0.5 else 0 for w in group_weights] for _ in eaters]
    weight_matrix = [[sum(gj * gi for gj, gi in zip(group_participation[j], group_participation[i]))
                      for j, _ in enumerate(eaters)] for i, _ in enumerate(eaters)]
    return weight_matrix


def weight_at_table(weights, table):
    return sum(weights[p] for p in table['participants'])


def adjust_weight_matrix(weights, placement):
    # TODO: Add badness points on all relations that are present at a table.
    pass


def calc_occasion_wrapper(args):
    execution_time, weights, participants, table_sizes = args
    return calc_occasion(execution_time, weights, participants, table_sizes)


def add_seatings(conference, participants):
    conference['placements'] = OrderedDict()
    for i, (name, table_sizes) in enumerate(zip(conference['seating_names'], conference['table_sizes'])):
        start = 0
        participants_by_table = []
        for size in table_sizes:
            participants_by_table.append([conference['staff_names'][p] for p in participants[i][start:start+size]])
            start += size

        conference['placements'][name] = participants_by_table


def calc_conference_wrapper(args):
    simulation_time, conference = args
    score, test_count, scramble_count, participants, relations = calc_conference(simulation_time,
                                                                                 conference['weight_matrix'],
                                                                                 conference['guests'],
                                                                                 conference['table_sizes'])
    return {'score': score, 'test_count': test_count, 'scramble_count': scramble_count,
            'participants': participants, 'relations': relations}


def chunks(l, n):
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

def create_relation_list(relations, conference):

    result = []

    # relations is a straight list, chunk it down to a matrix like list of lists
    for i, rel in enumerate(chunks(relations, len(conference['staff_names']))):
        for j, count in enumerate(rel[:i]):
            if count > 0:
                result.append(('%s - %s' % (conference['staff_names'][i], conference['staff_names'][j]),
                              count, conference['weight_matrix'][i][j]))

    # Sort on times seated at the same table and badness
    return sorted(result, key=lambda x: (x[1], x[2]), reverse=True)


def run_global_simulation(source_filename, destination_filename, simulation_time):
    conference = read_conference_data(filename=source_filename)

    pool_size = multiprocessing.cpu_count()
    pool = multiprocessing.Pool(processes=pool_size)

    start = time()
    results = pool.map(calc_conference_wrapper, pool_size * [[simulation_time, conference]])
    duration = time() - start

    pool.close()
    pool.join()

    best_result = min(results, key=lambda r: r['score'])
    test_count = sum(r['test_count'] for r in results)
    scramble_count = sum(r['scramble_count'] for r in results)

    add_seatings(conference, best_result['participants'])
    write_seating(conference, filename=destination_filename)
    relation_list = create_relation_list(best_result['relations'], conference)
    add_global_simulation_info(best_result['score'], test_count, scramble_count, duration,
                               relation_list, filename=destination_filename)



        # TODO:
        # - Would be nice to be able to select
        #   * No optimization, only scrambling
        #   * Optimization on every scramble
        #   * Optimization on best scramble
        # - Some way of specifying a multiplication factor for the relations to push
        #   persons away from each other?
        # - Some basic styling of the input form (bootstrap?)
        # - Add a pivot table showing the number of relations by times they were seated
        #   together (their score in the relation matrix, right now the number of times
        #   seated).
        # - Add a list of all participant sorted by name per event with the table number
        #   after.

def calculate_new_weights(weight_matrix, relations):
    flat_matrix = [(w + 1) * (2 ** (r - 1)) if r > 0 else 0 for w, r in zip(itertools.chain(*weight_matrix), relations)]
    return list(chunks(flat_matrix, len(weight_matrix)))


def run_linear_simulation(source_filename, destination_filename, simulation_time):
    conference = read_conference_data(filename=source_filename)

    pool_size = multiprocessing.cpu_count()
    pool = multiprocessing.Pool(processes=pool_size)

    occasion_count = len(conference['seating_names'])
    execution_time = simulation_time / occasion_count

    placements = []
    relation_matrices = []
    total_iteration_count = 0
    total_tests_count = 0

    weight_matrix = conference['weight_matrix']
    start = time()
    for i in range(occasion_count):

        # No use to waste CPU cycles if there is only one table, we can't do anything
        time_to_run = execution_time if len(conference['table_sizes'][i]) > 0 else 0.0
        placement_candidates = pool.map(calc_occasion_wrapper,
                                        pool_size * [[time_to_run,
                                                      weight_matrix,
                                                      conference['guests'][i],
                                                      conference['table_sizes'][i]]])
        total_iteration_count += sum(x[0] for x in placement_candidates)
        total_tests_count += sum(x[2] for x in placement_candidates)

        iteration_count, score, tests_count, seatings, relations = min(placement_candidates, key=lambda x: x[1])
        placements.append(seatings)
        relation_matrices.append(relations)

        # This recalculation of the weight matrix makes things much worse than they would
        # be without it. Just remove it and try...
        weight_matrix = calculate_new_weights(weight_matrix, relations)

    stop = time()

    add_seatings(conference, placements)
    write_seating(conference, filename=destination_filename)

    total_relations = [sum(r) for r in zip(*relation_matrices)]

    # The same calculation that is done in the C code for the global optimization
    score = sum(itertools.chain(*calculate_new_weights(conference['weight_matrix'], total_relations)))
    relation_list = create_relation_list(total_relations, conference)
    add_global_simulation_info(score, total_tests_count, total_iteration_count, stop - start,
                               relation_list, filename=destination_filename)

    pool.close()
    pool.join()
