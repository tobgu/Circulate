import os
from flask import Flask, request, redirect, url_for, render_template
import simplejson
from werkzeug.utils import secure_filename
from diner import run_global_simulation, run_linear_simulation

UPLOAD_FOLDER = 'uploads/'
RESULT_FOLDER = 'results/'
ALLOWED_EXTENSIONS = set(['xls', 'xlsm'])


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


IS_DEVELOP_MODE = True
import os.path

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

            # Solution to avoid having to rerun the simulation all the time
            if os.path.isfile("cache.json") and IS_DEVELOP_MODE:
                with open("cache.json", mode='r') as f:
                    conference_json = f.readline()
                    staff_names_json = f.readline()
            else:
                data = run_simulation(full_filename,
                               os.path.join(app.config['RESULT_FOLDER'], result_filename),
                               simulation_time=float(simulation_time),
                               climb_mode=int(climb_mode))

                conference_json = simplejson.dumps([{'name': name, 'tables': tables} for name, tables in data['conference']['placements'].iteritems()])
                staff_names_json = simplejson.dumps(data['conference']['staff_names'])

                if IS_DEVELOP_MODE:
                    with open("cache.json", mode='w') as f:
                        f.writelines([conference_json + '\n', staff_names_json])

            return render_template('show_participants.html',
                                   conference=conference_json,
                                   staff_names=staff_names_json)
#            return redirect(url_for('download_file', filename=result_filename))

    return '''
    <!doctype html>
    <style>
        .smart-green {
            width: 400px;
            margin-right: auto;
            margin-left: auto;
            background: #FFF;
            padding: 30px 30px 20px 30px;
            box-shadow: rgba(194, 194, 194, 0.7) 0 3px 10px -1px;
            -webkit-box-shadow: rgba(194, 194, 194, 0.7) 0 3px 10px -1px;
            font: 12px Arial, Helvetica, sans-serif;
            color: #666;
            border-radius: 5px;
            -webkit-border-radius: 5px;
            -moz-border-radius: 5px;
        }
        .smart-green h1 {
            font: 24px "Trebuchet MS", Arial, Helvetica, sans-serif;
            padding: 20px 0px 20px 40px;
            display: block;
            margin: -30px -30px 10px -30px;
            color: #FFF;
            background: #9DC45F;
            text-shadow: 1px 1px 1px #949494;
            border-radius: 5px 5px 0px 0px;
            -webkit-border-radius: 5px 5px 0px 0px;
            -moz-border-radius: 5px 5px 0px 0px;
            border-bottom:1px solid #89AF4C;

        }

        .smart-green h1>span {
            display: block;
            font-size: 11px;
            color: #FFF;
        }

        .smart-green label {
            display: block;
            margin: 0px 0px 5px;
        }

        .smart-green label>span {
            float: left;
            margin-top: 10px;
            color: #5E5E5E;
        }

        .smart-green input[type="text"], .smart-green input[type="email"], .smart-green textarea, .smart-green select {
            color: #555;
            height:24px;
            width: 96%;
            padding: 3px 3px 3px 10px;
            margin-top: 2px;
            margin-bottom: 16px;
            border: 1px solid #E5E5E5;
            background: #FBFBFB;
            outline: 0;
            -webkit-box-shadow: inset 1px 1px 2px rgba(238, 238, 238, 0.2);
            box-shadow: inset 1px 1px 2px rgba(238, 238, 238, 0.2);
            font: normal 14px/14px Arial, Helvetica, sans-serif;
        }

        .smart-green select {
            background: url('down-arrow.png') no-repeat right, -moz-linear-gradient(top, #FBFBFB 0%, #E9E9E9 100%);
            background: url('down-arrow.png') no-repeat right, -webkit-gradient(linear, left top, left bottom, color-stop(0%,#FBFBFB), color-stop(100%,#E9E9E9));
           appearance:none;
            -webkit-appearance:none;
           -moz-appearance: none;
            text-indent: 0.01px;
            text-overflow: '';
            width:100%;
            height:30px;
        }

        .smart-green .button {
            background-color: #9DC45F;
            border-radius: 5px;
            -webkit-border-radius: 5px;
            -moz-border-border-radius: 5px;
            border: none;
            padding: 10px 25px 10px 25px;
            color: #FFF;
            text-shadow: 1px 1px 1px #949494;
        }

        .smart-green .button:hover {
            background-color:#80A24A;
        }
    </style>


    <title>Get seated!</title>
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
        <span>Simulation method:</span>
          <select name="simulation_method">
            <option value="global">Whole conference</option>
            <option value="occasion">Occasion by occasion</option>
          </select>
      <label>
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
    '''

from flask import send_from_directory


@app.route('/downloads/<filename>')
def download_file(filename):
    return send_from_directory(app.config['RESULT_FOLDER'], filename)



if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int("8000"), debug=True)