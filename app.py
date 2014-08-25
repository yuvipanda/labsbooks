import os
from flask import Flask
from IPython.config import Config
from IPython.nbconvert import HTMLExporter
from IPython.nbformat import current as nbformat

app = Flask(__name__)

@app.route('/<string:user>/<path:path>')
def display(user, path):
    full_path = os.path.join('/home', user, 'notebooks', path + '.ipynb')
    if not os.path.exists(full_path):
        return "No such notebook", 404
    exportHtml = HTMLExporter(config=Config({'HTMLExporter':{'default_template':'basic'}}))
    notebook = nbformat.reads_json(open(full_path).read())
    body, res = exportHtml.from_notebook_node(notebook)
    return body

if __name__ == '__main__':
    app.run(debug=True)
