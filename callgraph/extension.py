import ast

from IPython.core.magic import (Magics, line_magic, line_cell_magic,
                                magics_class, needs_local_scope)
from IPython.display import SVG, display
from IPython.testing.skipdoctest import skip_doctest

from .recorder import CallGraphRecorder
from .instrumentor import CallGraphInstrumentor


@magics_class
class CallGraphMagics(Magics):
    @skip_doctest
    @line_cell_magic
    @needs_local_scope
    def callgraph(self, line, local_ns=None):
        """Display the dynamic call graph for a Python statement or expression.

        Usage:
          %callgraph nchoosek(5, 2)

        This magic instruments global functions that are named in the statement.
        On completion, the functions are restored to their original values.

        The magic knows about functions that are decorated with functools.lru_cache.
        Two calls with the same arguments to a cached function will display as
        the same node. For simplicity, "same" to the instrumentation just means
        same string representation. It also ignores the `maxsize` and `typed`
        arguments to lru_cache.

        Options:

        -h: display the graph “horizontally”, with function calls running from left to right.

        -r: reverse the graph (display arrows from callee to caller). Label the arrows with the return values.

        -w<N>: max width of the graph

        --no-clear: Don't clear lru_cache caches before execution.

        Examples
        --------
        ```
        from functools import lru_cache

        @lru_cache()
        def nchoosek(n, k):
            if k == 0:
                return 1
            if n == k:
                return 1
            return nchoosek(n - 1, k - 1) + nchoosek(n - 1, k)

        %callgraph nchoosek(5, 2)
        %callgraph nchoosek(5, 2); nchoosek(5, 3)
        %callgraph -r nchoosek(5, 2)
        ```
        """
        # Some constants.
        filename = '<magic callgraph>'
        mode = 'exec'

        opts, stmt = self.parse_options(line, 'w:ehr', 'no-clear', posix=False)

        # Parse the options. Create a call graph recorder with those options.
        options = {'graph_attrs': {}}
        if 'e' in opts:
            options['equal'] = True
        if 'r' in opts:
            options['label_returns'] = True
        if 'h' in opts:
            options['graph_attrs']['rankdir'] = 'LR'
        if 'w' in opts:
            options['graph_attrs']['size'] = '{},'.format(opts['w'])
        recorder = CallGraphRecorder(**options)

        # Parse the statement. Collect calls to instrument.
        tree = ast.parse(stmt, filename=filename, mode=mode)
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
        fn_names = [n.func.id for n in calls if isinstance(n.func, ast.Name)]

        if 'no-clear' not in opts:
            fns = (local_ns[name] for name in fn_names if name in local_ns)
            clear_fns = filter(
                None, (getattr(fn, 'cache_clear', None) for fn in fns))
            list(c() for c in clear_fns if hasattr(c, '__call__'))

        # For now, only global variables (`a(x)`) are instrumented, not
        # attributes (`a.b(x)`). The following would collect attributes
        # ("qualified" function calls).
        # qfns = list(n.func for n in calls if isinstance(n.func, ast.Attribute))

        with CallGraphInstrumentor(fn_names, recorder=recorder, local_ns=local_ns) as recorder:
            exec(compile(tree, filename=filename, mode=mode), local_ns)
            display(SVG(data=recorder.graph._repr_svg_()))


def load_ipython_extension(ipython):
    "Register the IPython magic."
    ipython.register_magics(CallGraphMagics)
