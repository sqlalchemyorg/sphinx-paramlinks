#!coding: utf-8
import re
from docutils import nodes
from docutils.transforms import Transform
import os
from sphinx.util.osutil import copyfile
from sphinx.util.console import bold
from sphinx.domains.python import PyXRefRole

def autodoc_process_docstring(app, what, name, obj, options, lines):
    # locate :param: lines within docstrings.  augment the parameter
    # name with that of the parent object name plus a token we can
    # spot later.
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

        # seach <strong> nodes, which will include the titles for
        # those :param: directives, looking for our special token.
        # then fix up the text within the node.
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
                    # add the "p" thing only if we're the HTML builder.
                    ref.parent.insert(len(ref.parent) - 2,
                        nodes.reference('', '',
                                nodes.Text(u"¶", u"¶"),
                                refid=refid,
                                classes=['paramlink']
                        )
                    )


def lookup_params(app, env, node, contnode):
    # here, we catch the "pending xref" nodes that we created with
    # the "paramref" role we added.   The resolve_xref() routine
    # knows nothing about this node type so it never finds anything;
    # the Sphinx BuildEnvironment then gives us one more chance to do a lookup
    # here.

    if node['reftype'] != 'paramref':
        return None

    target = node['reftarget']

    tokens = target.split(".")
    resolve_target = ".".join(tokens[0:-1])
    paramname = tokens[-1]

    domain = env.domains['py']
    refdoc = node.get('refdoc', None)

    # we call the same "resolve_xref" that BuildEnvironment just tried
    # to call for us, but we load the call with information we know
    # it can find, e.g. the "object" role (or we could use :meth:/:func:)
    # along with the classname/methodname/funcname minus the parameter
    # part.
    newnode = domain.resolve_xref(env, refdoc, app.builder,
                                  "obj", resolve_target, node, contnode)

    if newnode is not None:
        # assuming we found it, tack the paramname back onto to the final
        # URI.
        newnode['refuri'] += ".params." + paramname
    return newnode

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

    # PyXRefRole is what the sphinx Python domain uses to set up
    # role nodes like "meth", "func", etc.  It produces a "pending xref"
    # sphinx node along with contextual information.
    app.add_role_to_domain("py", "paramref", PyXRefRole())

    app.connect('autodoc-process-docstring', autodoc_process_docstring)
    app.connect('builder-inited', add_stylesheet)
    app.connect('build-finished', copy_stylesheet)
    app.connect('missing-reference', lookup_params)

