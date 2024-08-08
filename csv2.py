from flask import Flask, request, render_template, redirect, url_for
import pandas as pd
import mysql.connector
from mysql.connector import Error
import os
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import difflib

# Initialize Flask app
app = Flask(__name__)

# Download NLTK data
nltk.download('punkt')
nltk.download('stopwords')

data_frame = None
connection = None
table_names = []


def connect_to_mysql_db(user, password, host, database):

    try:
        connection = mysql.connector.connect(
            user=user,
            password=password,
            host=host,
            database=database
        )
        if connection.is_connected():
            print("Connected to MySQL Database")
            return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
    return None


def fetch_table_names(connection):

    table_names = []
    try:
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES")
        for table in cursor.fetchall():
            table_names.append(table[0])
        cursor.close()
    except Error as e:
        print(f"Error fetching tables: {e}")
    return table_names


def load_table_data(connection, table_name):
    """
    Load table data into a DataFrame.
    """
    try:
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql(query, connection)
        return df
    except Exception as e:
        print(f"Error loading table data: {e}")
        return pd.DataFrame()


def autocorrect_keywords(word, possibilities, cutoff=0.7):
    """
    Autocorrect given word using difflib.
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
        'greater': ['greater', 'grater', 'grtr', 'gretar', 'grtrt'],
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
def show_tables():
    global connection, table_names

    # Connection details
    user = "root"
    password = "Vibhu123&"
    host = "127.0.0.1"
    database = "csv_data_db"

    # Connect to MySQL database
    connection = connect_to_mysql_db(user, password, host, database)

    # Fetch table names
    table_names = fetch_table_names(connection)

    if request.method == 'POST':
        if 'next' in request.form:
            selected_table = request.form.get('table')
            global data_frame
            data_frame = load_table_data(connection, selected_table)
            return redirect(url_for('display_table'))

    return render_template('tables.html', tables=table_names)


@app.route('/display_table', methods=['GET', 'POST'])
def display_table():
    global data_frame
    if request.method == 'POST':
        if 'next' in request.form:
            return redirect(url_for('query_page'))
        elif 'back' in request.form:
            return redirect(url_for('show_tables'))

    return render_template('display_table.html', tables=[data_frame.to_html(classes='data', header="true")])


@app.route('/query', methods=['GET', 'POST'])
def query_page():
    global data_frame
    if request.method == 'POST':
        user_query = request.form.get('query')
        result = parse_query(user_query, data_frame)
        return render_template('query.html', tables=[result.to_html(classes='data', header="true")])
    return render_template('query.html')


if __name__ == '__main__':
    app.run(debug=True)
