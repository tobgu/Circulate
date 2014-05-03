import os
from flask import Flask, request, url_for, render_template
import simplejson
from werkzeug.utils import secure_filename
from diner import run_simulation, CLIMB_MODE_ALWAYS, seatings_to_guest_list
from xlsm_io import read_conference_data, write_simulation_result

UPLOAD_FOLDER = 'uploads/'
RESULT_FOLDER = 'results/'
ALLOWED_EXTENSIONS = set(['xls', 'xlsm'])
IS_DEVELOP_MODE = True


class CustomFlask(Flask):
    jinja_options = Flask.jinja_options.copy()
    jinja_options.update(dict(
        block_start_string='<%',
        block_end_string='%>',
        variable_start_string='%%',
        variable_end_string='%%',
        comment_start_string='<#',
        comment_end_string='#>',
    ))

app = CustomFlask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

# TODO
# - Make conflict listing better
def run_simulation_from_json(json_data, simulation_time):
    guests, table_sizes, seating_names = seatings_to_guest_list(json_data['conference'])
    conference = {'weight_matrix': json_data['weight_matrix'], 'guests': guests,
                  'table_sizes': table_sizes, 'seating_names': seating_names,
                  'staff_names': json_data['participant_names'],
                  'coloc_penalty': json_data['coloc_penalty']}

    return run_simulation(conference, simulation_time, CLIMB_MODE_ALWAYS)


@app.route('/simulate', methods=['POST'])
def simulate():
    # TODO: Fix mismatch in conference naming
    result = run_simulation_from_json(request.json, request.json['simulation_time'])
    return simplejson.dumps({'relations': result['relations'],
                             'conference': result['conference']['placements'],
                             'relation_stats': result['conference']['relation_stats']})


@app.route('/result/excel', methods=['POST'])
def generate_excel():
    # Generate excel file and provide link to document.

    result = run_simulation_from_json(request.json, 0.0)
    result_filename = 'result.xls'
    destination = os.path.join(app.config['RESULT_FOLDER'], result_filename)
    write_simulation_result(result, filename=destination)

    return simplejson.dumps({'url': url_for('download_file', filename=result_filename)})

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']

        # The magic numbers in the climb mode are coordinated with the C-code
        climb_mode = request.form['climb_mode']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            full_filename = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(full_filename)

            # Solution to avoid having to rerun the simulation all the time
            if os.path.isfile("cache.json") and IS_DEVELOP_MODE:
                with open("cache.json", mode='r') as f:
                    conference_json = f.readline()
                    staff_names_json = f.readline()
                    relations_json = f.readline()
                    weight_matrix_json = f.readline()
                    relation_stats_json = f.readline()
                    group_names_json = f.readline()
                    group_participation_json = f.readline()
            else:
                # Load initial data into system by running a 0 second simulation
                conference = read_conference_data(filename=full_filename)
                conference['coloc_penalty'] = 0
                data = run_simulation(conference, simulation_time=0.0, climb_mode=int(climb_mode))
                conference_json = simplejson.dumps(conference['placements'])
                staff_names_json = simplejson.dumps(data['conference']['staff_names'])
                relations_json = simplejson.dumps(data['relations'])
                weight_matrix_json = simplejson.dumps(data['conference']['weight_matrix'])
                relation_stats_json = simplejson.dumps(data['conference']['relation_stats'])
                group_names_json = simplejson.dumps(data['conference']['group_names'])
                group_participation_json = simplejson.dumps(data['conference']['group_participation'])

                if IS_DEVELOP_MODE:
                    with open("cache.json", mode='w') as f:
                        f.writelines([conference_json + '\n',
                                      staff_names_json + '\n',
                                      relations_json + '\n',
                                      weight_matrix_json + '\n',
                                      relation_stats_json + '\n',
                                      group_names_json + '\n',
                                      group_participation_json])

            return render_template('show_participants.html',
                                   conference=conference_json,
                                   staff_names=staff_names_json,
                                   relations=relations_json,
                                   weight_matrix=weight_matrix_json,
                                   relation_stat=relation_stats_json,
                                   group_names=group_names_json,
                                   group_participation=group_participation_json)

    return '''
    <!doctype html>
    <html>
        <head>
          <meta charset="UTF-8">
          <link rel="stylesheet" type="text/css" href="/static/styles.css">
          <title>Get seated!</title>
        </head>

        <body>
            <form class="smart-green" action="" method=post enctype=multipart/form-data>
              <h1>Get seated!
                <span>Select input file and parameters. <a href="/downloads/seating.xlsm">Demo file</a></span>
              </h1>
              <label>
                <input type=file name=file />
              </label>
              <label>
                <span>Hill climb:</span>
                  <select name="climb_mode">
                    <option value="1">Always</option>
                    <option value="2">Never</option>
                  </select>
              <label>
              <label>
                <span>&nbsp;</span>
                <input class="button" type=submit value=Run>
              </label>
            </form>
        </body>
    </html>
    '''

from flask import send_from_directory


@app.route('/downloads/<filename>')
def download_file(filename):
    return send_from_directory(app.config['RESULT_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int("8000"), debug=True)