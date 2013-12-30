#!coding: utf-8
import re
from docutils import nodes
from docutils.transforms import Transform
import os
from sphinx.util.osutil import copyfile
from sphinx.util.console import bold

def autodoc_process_docstring(app, what, name, obj, options, lines):

    def _cvt_param(name, line):
        def cvt(m):
            return ":param %s_sphinx_paramlinks_%s.%s:" % (
                            m.group(1) or '', name, m.group(2))
        return re.sub(r'^:param ([^:]+? )?([^:]+?):', cvt, line)

    if what in ('function', 'method', 'class'):
        lines[:] = [_cvt_param(name, line) for line in lines]

class LinkParams(Transform):
    default_priority = 210

    def apply(self):
        is_html = self.document.settings.env.app.builder.name == 'html'

        for ref in self.document.traverse(nodes.strong):
            text = ref.astext()
            if text.startswith("_sphinx_paramlinks_"):
                components = re.match(r'_sphinx_paramlinks_(.+)\.(.+)$', text)
                location, paramname = components.group(1, 2)

                refid = "%s.params.%s" % (location, paramname)
                ref.parent.insert(0,
                    nodes.target('', '', ids=[refid])
                )
                del ref[0]
                ref.insert(0, nodes.strong(paramname, paramname))

                if is_html:
                    ref.parent.insert(len(ref.parent) - 2,
                        nodes.reference('', '',
                                nodes.Text(u"¶", u"¶"),
                                refid=refid,
                                classes=['paramlink']
                        )
                    )


def make_param_ref(name, rawtext, text, lineno, inliner, options={}, content=[]):
    import pdb
    pdb.set_trace()
    prefix = "#%s"
    ref = "foo"
    node = nodes.reference(rawtext, prefix % text, refuri=ref, **options)
    return [node], []


def add_stylesheet(app):
    app.add_stylesheet('sphinx_paramlinks.css')

def copy_stylesheet(app, exception):
    if app.builder.name != 'html' or exception:
        return
    app.info(bold('Copying sphinx_paramlinks stylesheet... '), nonl=True)
    dest = os.path.join(app.builder.outdir, '_static', 'sphinx_paramlinks.css')
    source = os.path.abspath(os.path.dirname(__file__))
    copyfile(os.path.join(source, "sphinx_paramlinks.css"), dest)
    app.info('done')

def setup(app):
    app.add_transform(LinkParams)
    app.connect('autodoc-process-docstring', autodoc_process_docstring)
    app.add_role('paramref', make_param_ref)
    app.connect('builder-inited', add_stylesheet)
    app.connect('build-finished', copy_stylesheet)

