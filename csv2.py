from flask import Flask, request, render_template, redirect, url_for
import pandas as pd
import os
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import difflib

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'

nltk.download('punkt')
nltk.download('stopwords')

csv_data = None


def autocorrect_keywords(word, possibilities, cutoff=0.7):
    """
    Autocorrect function to correct keywords using difflib.
    Finds the closest match for a given word from a list of possibilities.
    """
    matches = difflib.get_close_matches(word, possibilities, n=1, cutoff=cutoff)
    if matches:
        return matches[0]
    return word


def parse_query(query, df):
    """
    Parse the user query and filter the DataFrame.
    The function supports 'greater than', 'less than', and 'equals to' operations.
    """
    # Tokenize the query
    tokens = word_tokenize(query.lower())

    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    filtered_tokens = [w for w in tokens if not w in stop_words]

    # Define basic operators and their autocorrect possibilities
    operator_keywords = {
        'greater': ['greater', 'grater', 'grtr', 'gretar', 'grtr', 'grtrt'],
        'less': ['less', 'les', 'lss', 'lessthan', 'lst'],
        'equals': ['equals', 'equal', 'eqals', 'eqls', 'equalto', 'eq'],
        'than': ['than', 'thn', 'tahn', 'taht']
    }

    # Correct the operators using difflib
    corrected_tokens = [autocorrect_keywords(token, sum(operator_keywords.values(), [])) for token in filtered_tokens]

    # Extract components for query execution
    column_name = None
    operator = None
    value = None

    # Detect operator
    operators = {
        'greater': '>',
        'less': '<',
        'equals': '=='
    }

    # Try to find columns, operators, and values
    for token in corrected_tokens:
        if token in df.columns.str.lower():
            column_name = token
        elif token in operators:
            operator = operators[token]
        else:
            try:
                # Attempt to convert token to a float for comparison
                value = float(token)
            except ValueError:
                value = token

    # Handle "greater than" or "less than"
    if "greater" in corrected_tokens and "than" in corrected_tokens:
        operator = '>'
    elif "less" in corrected_tokens and "than" in corrected_tokens:
        operator = '<'

    # Query validation
    if column_name and operator and value is not None:
        try:
            # Actual column name retrieval
            column_name_actual = df.columns[df.columns.str.lower() == column_name][0]
            # Perform the query
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
