from collections import OrderedDict
from random import random, sample
import multiprocessing
from time import time
from xlsm_io import read_conference_data, write_seating, add_global_simulation_info
from dinerc import calc_tables, calc_conference


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


def do_calculation_c(arg):
    from dinerc import calc_tables
    execution_time, weights, participants, table_sizes = arg
    iterations, result = calc_tables(execution_time, weights, participants, table_sizes)

    print "Iterations: %s, best result: %s" % (iterations, result)
    return {'total_score': result}


def group_seatings(conference, participants):
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


def create_relation_list(relations, conference):
    def chunks(l, n):
        for i in xrange(0, len(l), n):
            yield l[i:i+n]

    result = []

    # relations is a straight list, chunk it down to a matrix like list of lists
    for i, rel in enumerate(chunks(relations, len(conference['staff_names']))):
        for j, count in enumerate(rel[:i]):
            if count > 0:
                result.append(('%s - %s' % (conference['staff_names'][i], conference['staff_names'][j]),
                              count, conference['weight_matrix'][i][j]))

    # Sort on times seated at the same table and badness
    return sorted(result, key=lambda x: (x[1], x[2]), reverse=True)


def run_simulation(source_filename, destination_filename, simulation_time):
    conference = read_conference_data(filename=source_filename)

    pool_size = multiprocessing.cpu_count()
    pool = multiprocessing.Pool(processes=pool_size)

    start = time()
    results = pool.map(calc_conference_wrapper, pool_size * [[simulation_time, conference]])
    duration = time() - start

    best_result = min(results, key=lambda r: r['score'])
    test_count = sum(r['test_count'] for r in results)
    scramble_count = sum(r['scramble_count'] for r in results)

    group_seatings(conference, best_result['participants'])
    write_seating(conference, filename=destination_filename)
    relation_list = create_relation_list(best_result['relations'], conference)
    add_global_simulation_info(best_result['score'], test_count, scramble_count, duration,
                               relation_list, filename=destination_filename)


def run():
    pool_size = multiprocessing.cpu_count()
    pool = multiprocessing.Pool(processes=pool_size)
    weights = calc_weight_matrix()
    participants_by_occasion = [sample(range(len(weights)), 100)]
    tables_by_occasion = [[4, 4, 4, 4, 4, 8, 8, 8, 8, 8, 10, 10, 10, 10]]
    execution_time = 1.0
    placementsc = []
    for x in range(1):
        for participants, table_sizes in zip(participants_by_occasion, tables_by_occasion):
            placement_candidates = pool.map(do_calculation_c, pool_size * [[execution_time, weights, participants, table_sizes]])
            placementsc.append(min(x['total_score'] for x in placement_candidates))

    pool.close()
    pool.join()

    print "Placements c, avg: %s, min: %s, max: %s" % (sum(placementsc)/float(len(placementsc)), min(placementsc), max(placementsc))


if __name__ == '__main__':
    run()
