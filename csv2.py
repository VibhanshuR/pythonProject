import os
from flask import Flask, request, redirect, url_for, render_template, send_from_directory
import pandas as pd
from werkzeug.utils import secure_filename
from sklearn.tree import DecisionTreeClassifier
import numpy as np

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    """Upload CSV File"""
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            return redirect(url_for('options', filename=filename))

    return render_template('upload.html')


@app.route('/options/<filename>', methods=['GET', 'POST'])
def options(filename):
    """Options Page to Re-upload or Proceed"""
    if request.method == 'POST':
        if 'reupload' in request.form:
            return redirect(url_for('upload_file'))
        elif 'proceed' in request.form:
            return redirect(url_for('rules', filename=filename))

    return render_template('options.html')


@app.route('/rules/<filename>', methods=['GET', 'POST'])
def rules(filename):
    """Apply Rules to the CSV"""
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    df = pd.read_csv(file_path)

    if request.method == 'POST':
        column_name = request.form['column_name']
        rule_type = request.form['rule_type']
        value = float(request.form['value'])

        if column_name in df.columns:
            if rule_type == 'gte':
                result_df = df[df[column_name] >= value]
            elif rule_type == 'lte':
                result_df = df[df[column_name] <= value]
            elif rule_type == 'eq':
                result_df = df[df[column_name] == value]
            elif rule_type == 'ml_gte':
                # Using ML Model to apply rule
                clf = DecisionTreeClassifier()
                # Assume the last column is the target variable
                X = df.drop(columns=[column_name])
                y = df[column_name] >= value
                clf.fit(X, y)
                predictions = clf.predict(X)
                result_df = df[predictions == True]
            else:
                return "Invalid rule type specified."

            result_filename = f"filtered_{filename}"
            result_file_path = os.path.join(app.config['UPLOAD_FOLDER'], result_filename)
            result_df.to_csv(result_file_path, index=False)

            return render_template('result2.html', tables=[result_df.to_html(classes='data')],
                                   titles=result_df.columns.values, filename=result_filename)

    return render_template('rules.html', columns=df.columns.tolist())


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Download the filtered CSV"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == "__main__":
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)
