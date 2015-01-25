from flask import Flask

# Very temporary file just to see if we can get anything at all out of openshift.

app = Flask(__name__)

@app.route('/')
@app.route('/hello')
def index():
    return "Hello from OpenShift"

if __name__ == '__main__':
    app.run()