from bottle import static_file, url, route, run, template, response, request
from pygments import highlight
from pygments.lexers import CLexer
from pygments.formatters import HtmlFormatter
from crh import *
from sys import argv
import json
import os

project_path = None
project      = None
analyzer     = None

lexer        = CLexer()
formatter    = HtmlFormatter(linenos=True, anchorlinenos=True, style="monokai", lineanchors="line")

showing_path = None

@route('/static/:path#.+#', name='static')
def static(path):
    return static_file(path, root='static')

@route('/search', method='POST')
def search_definition():
    pattern  = request.forms.get('pattern')
    partial  = request.forms.get('partial')
    samefile = request.forms.get('samefile')
    kind     = request.forms.get('kind')

    records     = None
    constraint  = None

    #### Build up constraint
    if partial:
      constraint = Definition.name.contains(pattern)
    else:
      constraint = Definition.name == pattern

    if samefile:
      constraint = (Definition.path == showing_path) & constraint

    if kind != "*":
      constraint = (Definition.kind == kind) & constraint

    #### Get records
    records = Definition.select().where(constraint).execute()
    return_data = []

    for record in records:
        data = dict(line=record.line, name=record.name, path=record.path, kind=record.kind)
        return_data.append(data)

    response.content_type = 'application/json; charset=utf-8'
    return_data = json.dumps(return_data)

    return return_data

@route('/tree')
def get_tree():
    tree = project.get_hierarchy()[0][0]['children']
    jq_tree_json = json.dumps(tree)
    response.content_type = 'application/json; charset=utf-8'

    return jq_tree_json

@route('/code/:path#.+#')
def get_code(path):
    hl_lines = []
    if request.query.line:
        hl_lines += [int(request.query.line)]

    formatter = HtmlFormatter(linenos=True, anchorlinenos=True, style="monokai", lineanchors="line", hl_lines=hl_lines)

    code = project.read_file(path)
    code = highlight(code, lexer, formatter)

    response.content_type = 'text/html; charset=utf-8'

    global showing_path
    showing_path = path

    return code

@route('/')
def index():
    return template('./views/index.tpl', get_url=url, project=project, analyzer=analyzer)

if __name__ == '__main__':
    project_path = argv[1]
    
    init_database(project_path)

    project  = Project(project_path)
    analyzer = Analyzer(project)

    analyzer.analyze_definition()

    run(host='localhost', port=8888, debug=True)
