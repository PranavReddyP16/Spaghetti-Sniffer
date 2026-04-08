import os
import sys
from flask import Flask, request, jsonify

from analyzers.unused_imports import find_unused_variables_and_imports
from analyzers.long_functions import find_long_functions
from analyzers.bad_exception_handler import find_bad_exception_handling
from analyzers.context_management import get_bad_context
from analyzers.dead_code import get_dead_code
from analyzers.cyclomatic_complexity import get_cyclomatic_complexity
from analyzers.hardcoded_values import get_hardcoded
from analyzers.deep_nesting import get_deep_nesting
from analyzers.too_many_params import get_too_many_params
from analyzers.variable_names import get_bad_variable_name
from analyzers.variable_usage import get_bad_variable_usage
from analyzers.bool_comparisons import get_bad_bool_comparisons
from analyzers.print_statements import get_print_statements
from analyzers.unnecessary_return_checks import get_unnecessary_checks
from analyzers.cross_file_duplicates import get_duplicate_multiple
from analyzers.cyclic_imports import get_cyclic
from lang import get_comment

app = Flask(__name__)

folder_insights_store = {}
file_contents = {}
cycle_data_global = {}


@app.route('/process', methods=['POST'])
def process_file_and_folder():
    data = request.get_json()
    file_content = data.get('fileContent', "")
    folder_content = data.get('folderContent', {})
    current_file = data.get('current_fileName')
    current_file = current_file.split("\\")[-1]

    highlights = process_file_content(file_content, folder_content, current_file)
    folder_insights = analyze_folder_contents(folder_content, current_file)
    return jsonify({
        "highlights": highlights,
        "folderInsights": folder_insights
    })


def process_file_content(file_content, folder_content, current_file):
    highlights = []

    unused_vars, unused_imports = find_unused_variables_and_imports(file_content)
    for imp in unused_imports:
        highlights.append({
            "line": unused_imports[imp],
            "suggestion": get_comment("unused imports" + imp),
            "tag": "unused"
        })
    for var in unused_vars:
        highlights.append({
            "line": unused_vars[var],
            "suggestion": get_comment("unused variables" + var),
            "tag": "unused"
        })

    long_functions = find_long_functions(file_content, max_length=50)
    for func_name, start_line, end_line, length in long_functions:
        highlights.append({
            "start_line": start_line,
            "end_line": end_line,
            "suggestion": get_comment("too long function" + func_name),
            "tag": "long"
        })

    bad_handlers = find_bad_exception_handling(file_content)
    for lineno in bad_handlers:
        highlights.append({
            "line": lineno,
            "suggestion": get_comment("bad exception handling"),
            "tag": "exception"
        })

    bad_context = get_bad_context(file_content)
    for context in bad_context:
        highlights.append({
            "line": context['line'],
            "suggestion": get_comment("file hasnt been opened safely"),
            "tag": "bad_context"
        })

    dead_context = get_dead_code(file_content)
    for context in dead_context:
        highlights.append({
            "line": context['line'],
            "suggestion": get_comment("dead code"),
            "tag": "dead_context"
        })

    cyclomatic_complex = get_cyclomatic_complexity(file_content)
    for complexity in cyclomatic_complex:
        if complexity['complexity'] > 5:
            highlights.append({
                "line": complexity['line'],
                "suggestion": get_comment("cyclomatic complexity too high"),
                "tag": "cyclomatic_complex"
            })

    hardcoded = get_hardcoded(file_content)
    for value in hardcoded:
        highlights.append({
            "line": value['line'],
            "suggestion": get_comment("no explanation for hardcoded value"),
            "tag": "hardcoded"
        })

    deep_nest = get_deep_nesting(file_content)
    for nest in deep_nest:
        highlights.append({
            "line": nest,
            "suggestion": get_comment("Nesting is too deep"),
            "tag": "deep_nesting"
        })

    too_many = get_too_many_params(file_content)
    for line in too_many:
        highlights.append({
            "line": line['line'],
            "suggestion": get_comment("too many params"),
            "tag": "too_many_params"
        })

    bad_variables = get_bad_variable_name(file_content)
    for line in bad_variables:
        highlights.append({
            "line": line,
            "suggestion": get_comment("bad variable name"),
            "tag": "bad_variable_name"
        })

    bad_var_usage = get_bad_variable_usage(file_content)
    for line in bad_var_usage:
        highlights.append({
            "line": line,
            "suggestion": get_comment("variable assigned multiple times before usage"),
            "tag": "bad_variable_usage"
        })

    bad_comparison = get_bad_bool_comparisons(file_content)
    for line in bad_comparison:
        highlights.append({
            "line": line,
            "suggestion": get_comment("unnecessary comparison against boolean literals"),
            "tag": "bad_bool_comparison"
        })

    statements = get_print_statements(file_content)
    for line in statements:
        highlights.append({
            "line": line,
            "suggestion": get_comment("print statements ill advised"),
            "tag": "print_statement"
        })

    unnecessary_checks = get_unnecessary_checks(file_content)
    for line in unnecessary_checks:
        highlights.append({
            "line": line,
            "suggestion": get_comment("Checking what the result is, then immediately returning that result, is redundant"),
            "tag": "unnecessary_return_check"
        })

    analyze_folder_contents(folder_content, current_file)

    if current_file in folder_insights_store:
        for line in folder_insights_store[current_file]:
            highlights.append(line)

    for data in cycle_data_global[current_file.split('.')[0]]:
        highlights.append({
            "line": data,
            "suggestion": get_comment("code contains cyclic import"),
            "tag": "cyclic_import"
        })

    return highlights


def analyze_folder_contents(folder_content, current_file):
    for filename, content in folder_content.items():
        if isinstance(content, dict):
            analyze_folder_contents(content, current_file)
        else:
            file_contents[filename] = content
            folder_insights_store[filename] = []
            cycle_data_global[filename.split('.')[0]] = []

    duplicate_multiple = get_duplicate_multiple(file_contents)
    cycle = get_cyclic(file_contents)

    for value in cycle.items():
        current_file_name = current_file.split('.')[0]
        if value[0] == current_file_name:
            cycle_data_global[current_file_name] = value[1]

    for duplicate in duplicate_multiple:
        for value in duplicate['lines']:
            if value[0] == current_file:
                folder_insights_store[value[0]].append({
                    "start_line": value[1],
                    "end_line": value[2],
                    "suggestion": get_comment("repetitive code"),
                    "tag": "multiple_duplicate"
                })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
