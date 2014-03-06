# Example groups
from random import random, sample
from time import time

groups = {'stockholm': {'tobias', 'erik', 'anders', 'simon', 'stefan'},
          'new_york': {'stanislav', 'joe', 'bill'},
          'triresolve': {'tobias', 'erik', 'anders', 'stanislav'},
          'trireduce': {'simon', 'stefan', 'joe', 'bill'}}

# - Create a matrix with all involved persons on each side.
# - All persons that are related within a group receive badness points on each others relations
# - There needs to be a table size or a number of tables defined with the size of each table (should the distance from
#   each other by the table also matter? What's the shape of the table?)
# - Once the first dinner has been computed (by optimizing on the minimum relation points per table) badness points
#   are added to all relations where people were sitting at the same table. Thereafter the next dinner is calculated and
#   the procedure is repeated.

# Observations
# - Only half of the matrix is relevant since a relation is reflexive, also no relations with one self need to be
#   investigated.
# - The score related to those that already are seated by the table must also be considered when placing a new person
#   at a table. Perhaps this is an iterative process rather than something that can be solved in one run? It's
#   probably some sort of optimization problem that can be solved using conventional methods...


# - Initial placement could be made simple by just splitting an existing group, at least to begin with
# - For each person to place loop over all tables and select the table that is not full with the least
#   badness points for that person. Place the person there.
# Perhaps it's better to make a set of all relations with a badness score for each relation. The badness
#

def calc_weight_matrix():
    eater_count = 200
    eaters = ['eater %s' % i for i in range(eater_count)]
    group_weights = [2, 1, 5, 2, 3, 1, 10, 2, 4, 7]
    group_participation = [[w if random() < 0.5 else 0 for w in group_weights] for _ in eaters]
    weight_matrix = [[sum(gj * gi for gj, gi in zip(group_participation[j], group_participation[i]))
                      for j, _ in enumerate(eaters)] for i, _ in enumerate(eaters)]
    return weight_matrix

import multiprocessing


def create_tables(mixed_participants, table_sizes, weights):
    # Entirely random placement
    # TODO: Test with replacing this with a more optimizing version and compare that to the results of
    #       this approach
    tables = []
    offset = 0
    for size in table_sizes:
        table_participants = mixed_participants[offset:offset+size]
        table_score = float(sum(sum(weights[table_participants[i]][j] for j in table_participants[i+1:])
                                for i in range(size - 1))) / size
        tables.append({'score': table_score, 'participants': table_participants})
        offset += size

    return tables


def create_tables(mixed_participants, table_sizes, weights):
    # Entirely random placement
    # TODO: Test with replacing this with a more optimizing version and compare that to the results of
    #       this approach
    tables = []
    offset = 0
    for size in table_sizes:
        table_participants = mixed_participants[offset:offset+size]
        table_score = float(sum(sum(weights[table_participants[i]][j] for j in table_participants[i+1:])
                                for i in range(size - 1))) / size
        tables.append({'score': table_score, 'participants': table_participants})
        offset += size

    return tables


def calc_table_score(table, participant, weights):
    return sum(weights[participant][other] for other in table['participants']) + table['score']


def weight_at_table(weights, table):
    return sum(weights[p] for p in table['participants'])

def find_heaviest_participant_for_tables(remaining_weights, tables_left):
    heaviest_participants = []
    for t in tables_left:
        heaviest_participants.append(max([(p, weight_at_table(w, t)) for p, w in remaining_weights.items()], key=lambda p: p[1]))
        del remaining_weights[heaviest_participants[-1][0]]

    return heaviest_participants


def place_participants(participants, tables, weights):
    # TODO: Some sort of initial placement (eg best table for each participant or best participant for each table,
    # is there a difference in performance or is it just arbitrary???)

    def calc_table_score(table, participant, weights):
        return sum(weights[participant][other] for other in table['participants']) + table['score']

    for p in participants:
        best_table = None
        for table in tables:
            if table['remaining_places'] > 0:
                score = calc_table_score(table, p[0], weights)
                if best_table is None or score < best_table[0]:
                    best_table = (score, table)

        best_table[1]['score'] = best_table[0]
        best_table[1]['participants'].append(p[0])
        best_table[1]['remaining_places'] -= 1


def create_tables3(mixed_participants, table_sizes, weights):
    tables = [{'score': 0, 'participants': [], 'remaining_places': size} for size in table_sizes]

    # Assume that all tables have at least two places
    tables_left = tables

    participant_set = set(mixed_participants)
    remaining_weights = dict((p_id, w) for p_id, w in enumerate(weights) if p_id in participant_set)

    # === Initial placement ===
    # Get those with the highest weights, perhaps it would be better to sort on the sum of the weights...
    heavy_participants = sorted(remaining_weights.items(), key=lambda x: sorted(x[1], reverse=True), reverse=True)[:len(tables_left)]

    # Prefer to place the heaviest participants at the smallest tables (this should make table size pulsate over time?)
    for hp, table in zip(heavy_participants, sorted(tables_left, key=lambda t: t['remaining_places'])):
        table['participants'].append(hp[0])
        table['remaining_places'] -= 1

    hp_ids = set(p[0] for p in heavy_participants)
    remaining_weights = dict((k, v) for k, v in remaining_weights.items() if k not in hp_ids)

    while tables_left:
        # Find the heaviest participant for each table
        heavy_participants = find_heaviest_participant_for_tables(remaining_weights, tables_left)

        place_participants(heavy_participants, tables_left, weights)

        tables_left = [t for t in tables if t['remaining_places'] > 0]

    # Weight the score of the table with the number of participants at the table
    for table in tables:
        table['score'] = float(table['score']) / len(table['participants'])
        del table['remaining_places']

    return tables

def create_tables2(mixed_participants, table_sizes, weights):
    # Fairly naive optimization of the seatings
    tables = [{'score': 0, 'participants': [], 'remaining_places': size} for size in table_sizes]
    for p in mixed_participants:
        best_table = None
        for table in tables:
            if table['remaining_places'] > 0:
                score = calc_table_score(table, p, weights)
                if best_table is None or score < best_table[0]:
                    best_table = (score, table)

        best_table[1]['score'] = best_table[0]
        best_table[1]['participants'].append(p)
        best_table[1]['remaining_places'] -= 1

    # Weight the score of the table with the number of participants at the table
    for table in tables:
        table['score'] = float(table['score']) / len(table['participants'])
        del table['remaining_places']

    return tables

def adjust_weight_matrix(weights, placement):
    # TODO: Add badness points on all relations that are present at a table.
    pass


def hill_climb(tables, weights):
    def _weight_at_table(participant, table):
        return sum(weights[participant][p] for p in table['participants'])

    def _hill_climb():
        for t1 in tables:
            for i1, p1 in enumerate(t1['participants']):
                w1_1 = _weight_at_table(p1, t1)
                for t2 in tables:
                    if t1 != t2:
                        for i2, p2 in enumerate(t2['participants']):
                            w2_2 = _weight_at_table(p2, t2)
                            t1['participants'][i1], t2['participants'][i2] = t2['participants'][i2], t1['participants'][i1]
                            w1_2 = _weight_at_table(p1, t2)
                            w2_1 = _weight_at_table(p2, t1)

                            if w1_2 + w2_1 < w1_1 + w2_2:
                                return True
                            else:
                                # Worse proposition
                                t1['participants'][i1], t2['participants'][i2] = t2['participants'][i2], t1['participants'][i1]

        # Local optimum found
        return False

    climbs = 0
    while _hill_climb():
#        print "Climb %s" % climbs
        climbs += 1

#    print "Number of climbs: %s" % climbs

    for t in tables:
        t['score'] = float(sum(sum(weights[t['participants'][i]][j] for j in t['participants'][i+1:])
                               for i in range(len(t['participants']) - 1))) / len(t['participants'])

    return tables


def create_tables4(mixed_participants, table_sizes, weights):
    # Pure hill climbing
    tables = create_tables(mixed_participants, table_sizes, weights)
    before = sum(t['score'] for t in tables)
    tables = hill_climb(tables, weights)
    after = sum(t['score'] for t in tables)
    print "Score before hill climbing: %s, after: %s" % (before, after)
    return tables


def do_calculation(arg):
    execution_time, weights, participants, table_sizes = arg
    start_time = time()
    max_time = start_time + execution_time
    iterations = 0
    best_tables = None
    score_history = []
    while time() < max_time:
        mixed_participants = sample(participants, len(participants))
        tables = create_tables3(mixed_participants, table_sizes, weights)
        total_score = sum(t['score'] for t in tables)
        score_history.append(total_score)
        if best_tables is None or total_score < best_tables['total_score']:
            # print 'Found better placement %s at iteration %s, time: %s' % (total_score, iterations, time() - start_time)
            best_tables = {'total_score': total_score, 'tables': tables}
        iterations += 1

    print 'Number of iterations: %s, average: %s, best: %s' % (iterations, sum(score_history) / iterations, best_tables['total_score'])
    return best_tables


def do_calculation_c(arg):
    from dinerc import calc_tables
    execution_time, weights, participants, table_sizes = arg
    iterations, result = calc_tables(execution_time, weights, participants, table_sizes)

    print "Iterations: %s, best result: %s" % (iterations, result)
    return {'total_score': result}


def run():
    pool_size = multiprocessing.cpu_count()
#    pool_size = 1
    pool = multiprocessing.Pool(processes=pool_size)
    weights = calc_weight_matrix()
    placement_list = []
#    participants_by_occasion = [range(len(weights))[0:100]]
    participants_by_occasion = [sample(range(len(weights)), 100)]
    tables_by_occasion = [[4, 4, 4, 4, 4, 8, 8, 8, 8, 8, 10, 10, 10, 10]]
    execution_time = 10.0
    placementsc = []
    placementspy = []
    for x in range(1):
        for participants, table_sizes in zip(participants_by_occasion, tables_by_occasion):
            placement_candidates = pool.map(do_calculation_c, pool_size * [[execution_time, weights, participants, table_sizes]])
            placementsc.append(min(x['total_score'] for x in placement_candidates))

#            placement_candidates = map(do_calculation, pool_size * [[execution_time, weights, participants, table_sizes]])
#            placementspy.append(min(x['total_score'] for x in placement_candidates))

    #        placement_list.append(placement)
    #        adjust_weight_matrix(weights, placement)
    pool.close()
    pool.join()

    print "Placements c, avg: %s, min: %s, max: %s" % (sum(placementsc)/float(len(placementsc)), min(placementsc), max(placementsc))
 #   print "Placements py, avg: %s, min: %s, max: %s" % (sum(placementspy)/float(len(placementspy)), min(placementspy), max(placementspy))


if __name__ == '__main__':
    run()
