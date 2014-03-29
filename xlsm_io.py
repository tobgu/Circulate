from openpyxl import load_workbook


def conference_data(filename='seating.xlsm'):
    wb = load_workbook(filename=filename)
    conference = {}
    conference['staff_names'], conference['weight_matrix'] = staff_info(wb)
    conference['seating_names'], conference['table_sizes'] = tables_sizes_per_seating(wb)
    conference['guests'] = guests_per_seating(wb)
    return conference


def tables_sizes_per_seating(wb):
    seatings = wb['Seatings']
    seating_names = [r[0].value for r in seatings.rows[2:] if r[0].value]
    table_sizes = [[c.value for c in r[4:] if c.value] for r in seatings.rows[2:]]
    return seating_names, table_sizes


def staff_info(wb):
    staff = wb['Staff']
    groups = zip((c.value for c in staff.rows[0][1:]), (c.value for c in staff.rows[1][1:]))
    participant_names = [r[0].value for r in staff.rows[2:]]
    group_participation = [[int(c.value) * groups[i][1] if c.value else 0 for i, c in enumerate(r[1:])] for r in staff.rows[2:]]
    weight_matrix = [[sum(gj * gi for gj, gi in zip(group_participation[j], group_participation[i]))
                      for j in range(len(participant_names))] for i in range(len(participant_names))]

    return participant_names, weight_matrix


def guests_per_seating(wb):
    guests = wb['Guests']
    seatings = [[i for i, r in enumerate(c[2:]) if r.value] for c in guests.columns[1:]]
    return seatings
