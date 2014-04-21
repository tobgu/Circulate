import os
from flask import Flask, request, redirect, url_for, render_template
import itertools
import simplejson
from werkzeug.utils import secure_filename
from diner import run_global_simulation, do_run_global_simulation, CLIMB_MODE_ALWAYS, add_seatings, seatings_to_guest_list

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
# - Continue simulation
# - Generate excel and make downloadable (including list sorted on participant name with table id listed)
# - Make conflict listing better
# - Experiment with higher punishment for sitting next to each other multiple times
@app.route('/simulate', methods=['POST'])
def simulate():
    data = request.json
    guests, table_sizes, seating_names = seatings_to_guest_list(data['conference'])
    conference = {'weight_matrix': data['weight_matrix'], 'guests': guests,
                  'table_sizes': table_sizes, 'seating_names': seating_names}
    best_result, _, relation_list, _, _ = do_run_global_simulation(CLIMB_MODE_ALWAYS, conference, 1.0)
    add_seatings(conference, best_result['participants'])

    conference = [{'name': name, 'tables': tables} for name, tables in conference['placements'].iteritems()]
    return simplejson.dumps({'relations': relation_list, 'conference': conference})


@app.route('/excel', methods=['POST'])
def generate_excel():
    # Generate excel file and provide link to document.
    pass

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        simulation_time = request.form['simulation_time']

        # The magic numbers in the climb mode are coordinated with the C-code
        climb_mode = request.form['climb_mode']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            full_filename = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(full_filename)
            result_filename = 'result_' + filename.rsplit('.', 1)[0] + '.xls'

            # Solution to avoid having to rerun the simulation all the time
            if os.path.isfile("cache.json") and IS_DEVELOP_MODE:
                with open("cache.json", mode='r') as f:
                    conference_json = f.readline()
                    staff_names_json = f.readline()
                    relations_json = f.readline()
                    weight_matrix_json = f.readline()
            else:
                data = run_global_simulation(full_filename,
                               os.path.join(app.config['RESULT_FOLDER'], result_filename),
                               simulation_time=float(simulation_time),
                               climb_mode=int(climb_mode))

                conference_json = simplejson.dumps([{'name': name, 'tables': tables} for name, tables in data['conference']['placements'].iteritems()])
                staff_names_json = simplejson.dumps(data['conference']['staff_names'])
                relations_json = simplejson.dumps(data['relations'])
                weight_matrix_json = simplejson.dumps(data['conference']['weight_matrix'])

                if IS_DEVELOP_MODE:
                    with open("cache.json", mode='w') as f:
                        f.writelines([conference_json + '\n', staff_names_json + '\n', relations_json + '\n', weight_matrix_json])

            return render_template('show_participants.html',
                                   conference=conference_json,
                                   staff_names=staff_names_json,
                                   relations=relations_json,
                                   weight_matrix=weight_matrix_json)
#            return redirect(url_for('download_file', filename=result_filename))

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
                <span>Select input file and parameters</span>
              </h1>
              <label>
                <input type=file name=file />
              </label>
              <label>
                <span>Simulation time:</span>
                  <select name="simulation_time">
                    <option value="1">1 s</option>
                    <option value="5">5 s</option>
                    <option value="10">10 s</option>
                    <option value="30">30 s</option>
                    <option value="60">1 min</option>
                    <option value="300">5 min</option>
                    <option value="1800">30 min</option>
                    <option value="3600">1 h</option>
                    <option value="21600">6 h</option>
                    <option value="43200">12 h</option>
                    <option value="86400">24 h</option>
                  </select>
                 </span>
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