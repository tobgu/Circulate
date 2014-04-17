from openpyxl import load_workbook, Workbook
from openpyxl.cell import get_column_letter
#from time import time


def write_seating(conference, filename='seating_out.xls'):
    wb = Workbook()
    ws = wb.active
    ws.title = "Seatings"

    for col_idx, (name, tables) in enumerate(conference['placements'].items()):
        col = get_column_letter(col_idx+1)
        row = 1
        ws.cell('%s%s' % (col, row)).value = name
        ws.cell('%s%s' % (col, row)).style.font.bold = True
        for i, table in enumerate(tables):
            row += 2
            ws.cell('%s%s' % (col, row)).value = "Table %s" % (i+1)
            ws.cell('%s%s' % (col, row)).style.font.bold = True
            for name in sorted([conference['staff_names'][p['id']] for p in table]):
                row += 1
                ws.cell('%s%s' % (col, row)).value = name

        ws.column_dimensions[col].width = 20.0

    wb.save(filename=filename)


def write_score(score, filename):
    wb = Workbook()
    ws = wb.active
    ws.title = "Seatings"
    ws.cell('A1').value = 'Score: %s' % score
    ws.column_dimensions['A'].width = 100.0
    wb.save(filename=filename)

def set_at_row(ws, row, name, value):
    ws.cell('A%s' % row).value = name
    ws.cell('A%s' % row).style.font.bold = True
    ws.cell('B%s' % row).value = value


def set_triplet_at_row(ws, row, a, b, c):
    ws.cell('A%s' % row).value = a
    ws.cell('B%s' % row).value = b
    ws.cell('C%s' % row).value = c


def add_global_simulation_info(score, tests_count, scramble_count, duration, relation_list, filename, conference):
    wb = load_workbook(filename=filename)
    ws = wb.create_sheet()
    ws.title = "Statistics"

    set_at_row(ws, 1, "Simulation score", score)
    set_at_row(ws, 2, "Simulated moves", tests_count)
    set_at_row(ws, 3, "Starting points", scramble_count)
    set_at_row(ws, 4, "Simulation duration", duration)

    ws.cell('A8').value = "Relation"
    ws.cell('B8').value = "At same table"
    ws.cell('C8').value = "Badness"
    row = 9
    for (p1, p2, count, badness) in relation_list:
        set_triplet_at_row(ws, row, '%s - %s' % (conference['staff_names'][p1], conference['staff_names'][p2]),
                           count, badness)
        row += 1

    ws.column_dimensions['A'].width = 30.0
    ws.column_dimensions['B'].width = 30.0
    ws.column_dimensions['C'].width = 30.0

    wb.save(filename=filename)


def read_conference_data(filename='seating.xlsm'):
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
    seatings = [[{'id': i, 'fix': False} for i, r in enumerate(c[2:]) if r.value] for c in guests.columns[1:]]
    return seatings
