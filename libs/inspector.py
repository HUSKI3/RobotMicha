import sys, textwrap, inspect, ast

class AnnotationsCollector(ast.NodeVisitor):
    def __init__(self):
        self.annotations = {}

    def visit_AnnAssign(self, node):
        if node.simple:
            self.annotations[node.target.id] = node.annotation

def func_frame(func, *args, **kwargs):
    frame = None
    trace = sys.gettrace()

    def snatch_locals(_frame, name, arg):
        nonlocal frame
        if frame is None and name == 'call':
            frame = _frame
            sys.settrace(trace)
        return trace

    sys.settrace(snatch_locals)
    try:
        result = func(*args, **kwargs)
    finally:
        sys.settrace(trace)
    return frame, result

def func_local_ann(func):
    source = textwrap.dedent(inspect.getsource(func))
    mod = ast.parse(source)
    assert mod.body and isinstance(mod.body[0],
                                   (ast.FunctionDef, ast.AsyncFunctionDef))
    collector = AnnotationsCollector()
    collector.visit(mod.body[0])
    return {
        name: ast.get_source_segment(source, node)
        for name, node in collector.annotations.items()
    }