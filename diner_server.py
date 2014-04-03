import os
from flask import Flask, request, redirect, url_for
from werkzeug.utils import secure_filename
from diner import run_global_simulation, run_linear_simulation

UPLOAD_FOLDER = 'uploads/'
RESULT_FOLDER = 'results/'
ALLOWED_EXTENSIONS = set(['xls', 'xlsm'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        simulation_time = request.form['simulation_time']
        simulation_method = request.form['simulation_method']

        # The magic numbers in the climb mode are coordinated with the C-code
        climb_mode = request.form['climb_mode']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            full_filename = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(full_filename)
            result_filename = 'result_' + filename.rsplit('.', 1)[0] + '.xls'

            run_simulation = run_linear_simulation if simulation_method == 'occasion' else run_global_simulation

            run_simulation(full_filename,
                           os.path.join(app.config['RESULT_FOLDER'], result_filename),
                           simulation_time=float(simulation_time),
                           climb_mode=int(climb_mode))

            return redirect(url_for('download_file', filename=result_filename))

    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form action="" method=post enctype=multipart/form-data>
      <p>Input file: <input type=file name=file>
      <p>Simulation time:
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
      <p>Simulation method:
      <select name="simulation_method">
        <option value="global">Global</option>
        <option value="occasion">Occasion</option>
      </select>
      <p>Hill climb:
      <select name="climb_mode">
        <option value="1">Always</option>
        <option value="2">Never</option>
      </select>
      <p><input type=submit value=Run>
    </form>
    '''

from flask import send_from_directory


@app.route('/downloads/<filename>')
def download_file(filename):
    return send_from_directory(app.config['RESULT_FOLDER'], filename)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int("8000"), debug=True)