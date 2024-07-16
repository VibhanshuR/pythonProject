from flask import Flask, render_template, request, jsonify

app = Flask(__name__)


# Home route to display the form
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        dob = request.form['dob']
        return render_template('base.html', name=name, age=age, dob=dob)
    return render_template('login.html')


@app.route('/submit', methods=['POST'])
def submit():
    if request.is_json:
        data = request.get_json()
        name = data.get('name')
        age = data.get('age')
        dob = data.get('dob')
        return render_template('base.html', name=name, age=age, dob=dob)
    return jsonify({"error": "Request must be JSON"}), 400


if __name__ == '__main__':
    app.run(debug=True)
