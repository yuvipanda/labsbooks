import os
import yaml
from flask import Flask
from IPython.config import Config
from IPython.nbconvert import HTMLExporter
from IPython.nbformat import current as nbformat
from redis import StrictRedis

__dir__ = os.path.dirname(__file__)

default_config = yaml.load(open(os.path.join(__dir__, 'default_config.yaml')))
config = yaml.load(open(os.path.join(__dir__, 'config.yaml')))

app = Flask(__name__)
app.config.update(default_config)
if config:
    app.config.update(config)

redis = StrictRedis(
    host=app.config['REDIS_HOST'],
    db=app.config['REDIS_DB']
)

def cache_key(*args):
    return '%s-%s' % (app.config['REDIS_PREFIX'], '-'.join(args))


@app.route('/<string:user>/<path:path>')
def display(user, path):
    full_path = os.path.join('/home', user, 'notebooks', path + '.ipynb')
    if not os.path.exists(full_path):
        return "No such notebook", 404
    mtime = str(os.stat(full_path).st_mtime)
    key = cache_key(user, path, mtime)
    cached = redis.get(key)
    if cached:
        return cached
    exportHtml = HTMLExporter(config=Config({'HTMLExporter':{'default_template':'basic'}}))
    notebook = nbformat.reads_json(open(full_path).read())
    body, res = exportHtml.from_notebook_node(notebook)
    redis.set(key, body)
    redis.expire(key, app.config['REDIS_EXPIRY_SECONDS'])
    return body

if __name__ == '__main__':
    app.run(debug=True)
