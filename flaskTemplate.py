from flask import Flask, render_template, request

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


if __name__ == '__main__':
    app.run(debug=True)
