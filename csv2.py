from flask import Flask, request, render_template, redirect, url_for
import pandas as pd
import os
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'

nltk.download('punkt')
nltk.download('stopwords')

csv_data = None


def parse_query(query, df):

    tokens = word_tokenize(query.lower())

    stop_words = set(stopwords.words('english'))
    filtered_tokens = [w for w in tokens if not w in stop_words]

    operators = {
        'greater': '>',
        'less': '<',
        'equals': '==',
        'equal': '=='
    }

    column_name = None
    operator = None
    value = None

    for token in filtered_tokens:
        if token in df.columns.str.lower():
            column_name = token
        elif token in operators:
            operator = operators[token]
        else:
            try:
                value = float(token)
            except ValueError:
                value = token

    if column_name and operator and value is not None:
        try:
            column_name_actual = df.columns[df.columns.str.lower() == column_name][0]
            if operator == '>':
                result = df[df[column_name_actual] > value]
            elif operator == '<':
                result = df[df[column_name_actual] < value]
            elif operator == '==':
                result = df[df[column_name_actual] == value]
            else:
                result = pd.DataFrame()

            return result
        except Exception as e:
            print("Error querying data:", e)
            return pd.DataFrame()

    return pd.DataFrame()


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']

        if file.filename == '':
            return redirect(request.url)
        if file:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            global csv_data
            csv_data = pd.read_csv(file_path)
            return redirect(url_for('navigation'))
    return render_template('upload.html')


@app.route('/navigation', methods=['GET', 'POST'])
def navigation():
    if request.method == 'POST':
        if 'reupload' in request.form:
            return redirect(url_for('upload_file'))
        elif 'next' in request.form:
            return redirect(url_for('query_page'))
    return render_template('options.html')


@app.route('/query', methods=['GET', 'POST'])
def query_page():
    global csv_data
    if request.method == 'POST':
        user_query = request.form.get('query')
        result = parse_query(user_query, csv_data)
        return render_template('rules.html', tables=[result.to_html(classes='data', header="true")])
    return render_template('rules.html')


if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
