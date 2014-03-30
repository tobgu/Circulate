from collections import OrderedDict
from random import random, sample
import multiprocessing
from xlsm_io import read_conference_data, write_seating
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
    return calc_conference(simulation_time, conference['weight_matrix'], conference['guests'], conference['table_sizes'])


def run_simulation(source_filename, destination_filename, simulation_time):
    conference = read_conference_data(filename=source_filename)

    pool_size = multiprocessing.cpu_count()
    pool = multiprocessing.Pool(processes=pool_size)

    results = pool.map(calc_conference_wrapper, pool_size * [[simulation_time, conference]])

    score, participants, relations = min(results, key=lambda r: r[0])
    group_seatings(conference, participants)
    write_seating(conference, filename=destination_filename)


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
