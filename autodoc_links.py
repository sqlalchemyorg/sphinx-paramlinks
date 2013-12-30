#! coding:utf-8
__version__ = '0.1.0'

import re
from docutils import nodes
from docutils.transforms import Transform
import os
from sphinx.util.osutil import copyfile
from sphinx.util.console import bold

def _adjust_rendered_mod_name(app, modname, objname):
    _convert_modname = app.env.config.autodoc_links_convert_modname
    if modname in _convert_modname:
        return _convert_modname[modname]
    elif (modname, objname) in _convert_modname:
        return _convert_modname[(modname, objname)]
    else:
        return modname

_track_autodoced = {}
_inherited_names = set()
def autodoc_process_docstring(app, what, name, obj, options, lines):

    def _cvt_param(name, line):
        def cvt(m):
            txt = ":param %s_autodoc_link_param_%s.%s:" % (
                            m.group(1) or '', name, m.group(2))
            return txt
        return re.sub(r'^:param ([^:]+? )?([^:]+?):', cvt, line)

    if what in ('function', 'method', 'class'):
        #if name == "sqlalchemy.sql.expression.update":
        #    import pdb
        #    pdb.set_trace()
        lines[:] = [_cvt_param(name, line) for line in lines]

    if what == "class":
        _track_autodoced[name] = obj

        # need to translate module names for bases, others
        # as we document lots of symbols in namespace modules
        # outside of their source
        bases = []
        for base in obj.__bases__:
            if base is not object:
                bases.append(":class:`%s.%s`" % (
                        _adjust_rendered_mod_name(app, base.__module__, base.__name__),
                        base.__name__))

        if bases:
            lines[:0] = [
                        "Bases: %s" % (", ".join(bases)),
                        ""
            ]


    elif what in ("attribute", "method") and \
        options.get("inherited-members"):
        m = re.match(r'(.*?)\.([\w_]+)$', name)
        if m:
            clsname, attrname = m.group(1, 2)
            if clsname in _track_autodoced:
                cls = _track_autodoced[clsname]
                for supercls in cls.__mro__:
                    if attrname in supercls.__dict__:
                        break
                if supercls is not cls:
                    _inherited_names.add("%s.%s" % (supercls.__module__, supercls.__name__))
                    _inherited_names.add("%s.%s.%s" % (supercls.__module__, supercls.__name__, attrname))
                    lines[:0] = [
                        ".. container:: inherited_member",
                        "",
                        "    *inherited from the* :%s:`~%s.%s.%s` *%s of* :class:`~%s.%s`" % (
                                    "attr" if what == "attribute"
                                    else "meth",
                                    _adjust_rendered_mod_name(app, supercls.__module__, supercls.__name__),
                                    supercls.__name__,
                                    attrname,
                                    what,
                                    _adjust_rendered_mod_name(app, supercls.__module__, supercls.__name__),
                                    supercls.__name__
                                ),
                        ""
                    ]

class LinkParams(Transform):
    default_priority = 210

    def apply(self):
        is_html = self.document.settings.env.app.builder.name == 'html'

        for ref in self.document.traverse(nodes.strong):
            text = ref.astext()
#            if "sqlalchemy.sql.expression.update" in text:
#                import pdb
#                pdb.set_trace()
            if text.startswith("_autodoc_link_param_"):
                components = re.match(r'_autodoc_link_param_(.+)\.(.+)$', text)
                location, paramname = components.group(1, 2)

                refid = "%s.%s" % (location, paramname)
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


def missing_reference(app, env, node, contnode):
    if node.attributes['reftarget'] in _inherited_names:
        return node.children[0]
    else:
        return None

def make_param_ref(name, rawtext, text, lineno, inliner, options={}, content=[]):
    prefix = "#%s"
    ref = "foo"
    node = nodes.reference(rawtext, prefix % text, refuri=ref, **options)
    return [node], []


def add_stylesheet(app):
    app.add_stylesheet('autodoc_links.css')

def copy_stylesheet(app, exception):
    if app.builder.name != 'html' or exception:
        return
    app.info(bold('Copying autodoc_links stylesheet... '), nonl=True)
    dest = os.path.join(app.builder.outdir, '_static', 'autodoc_links.css')
    source = os.path.abspath(os.path.dirname(__file__))
    copyfile(os.path.join(source, "autodoc_links.css"), dest)
    app.info('done')

def setup(app):
    app.add_config_value("autodoc_links_convert_modname", {}, 'env')
    app.add_transform(LinkParams)
    app.connect('autodoc-process-docstring', autodoc_process_docstring)
    app.connect('missing-reference', missing_reference)
    app.add_role('paramref', make_param_ref)
    app.connect('builder-inited', add_stylesheet)
    app.connect('build-finished', copy_stylesheet)

