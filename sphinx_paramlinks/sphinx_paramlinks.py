#!coding: utf-8
from enum import Enum
import os
import re

from docutils import nodes
from docutils.transforms import Transform
from sphinx import addnodes
from sphinx.domains import ObjType
from sphinx.domains.python import ObjectEntry
from sphinx.domains.python import PythonDomain
from sphinx.domains.python import PyXRefRole
from sphinx.util import logging
from sphinx.util.console import bold
from sphinx.util.osutil import copyfile


# the searchindex.js system relies upon the object types
# in the PythonDomain to create search entries

PythonDomain.object_types["parameter"] = ObjType("parameter", "param")

LOG = logging.getLogger(__name__)


def _is_html(app):
    return app.builder.name in ("html", "readthedocs")


# https://www.sphinx-doc.org/en/master/extdev/deprecated.html


# Constants for link styles
class HyperlinkStyle(Enum):
    NONE = "none"
    NAME = "name"
    LINK_SYMBOL = "link_symbol"
    NAME_AND_SYMBOL = "name_and_symbol"


def _indexentries(env):
    return env.domains["index"].entries


def _tempdata(app):
    if "_sphinx_paramlinks_index" in _indexentries(app.env):
        idx = _indexentries(app.env)["_sphinx_paramlinks_index"]
    else:
        _indexentries(app.env)["_sphinx_paramlinks_index"] = idx = {}
    return idx


def autodoc_process_docstring(app, what, name, obj, options, lines):
    # locate :param: lines within docstrings.  augment the parameter
    # name with that of the parent object name plus a token we can
    # spot later.  Also put an index entry in a temporary collection.

    idx = _tempdata(app)

    docname = app.env.temp_data.get("docname")
    if not docname:
        return
    if docname in idx:
        doc_idx = idx[docname]
    else:
        idx[docname] = doc_idx = []

    def _cvt_param(name, line):
        if name.endswith(".__init__"):
            # kill off __init__ if present, the links are always
            # off the class
            name = name[0:-9]

        def cvt(m):
            role, modifier, objname, paramname = (
                m.group(1),
                m.group(2) or "",
                name,
                m.group(3),
            )
            refname = _refname_from_paramname(paramname, strip_markup=True)
            item = (
                "single",
                "%s (%s parameter)" % (refname, objname),
                "%s.params.%s" % (objname, refname),
                "",
            )
            item += (None,)

            doc_idx.append(item)
            return ":%s %s_sphinx_paramlinks_%s.%s:" % (
                role,
                modifier,
                objname,
                paramname,
            )

        def secondary_cvt(m):
            role, modifier, objname, paramname = (
                m.group(1),
                m.group(2) or "",
                name,
                m.group(3),
            )
            return ":%s %s_sphinx_paramlinks_%s.%s:" % (
                role,
                modifier,
                objname,
                paramname,
            )

        line = re.sub(r"^:(keyword|param) ([^:]+? )?([^:]+?):", cvt, line)
        line = re.sub(
            r"^:(kwtype|type) ([^:]+? )?([^:]+?):", secondary_cvt, line
        )
        return line

    if what in ("function", "method", "class"):
        lines[:] = [_cvt_param(name, line) for line in lines]


def _refname_from_paramname(paramname, strip_markup=False):
    literal_match = re.match(r"^``(.+?)``$", paramname)
    if literal_match:
        paramname = literal_match.group(1)
    refname = paramname
    eq_match = re.match(r"(.+?)=.+$", refname)
    if eq_match:
        refname = eq_match.group(1)
    if strip_markup:
        refname = re.sub(r"\\", "", refname)
    return refname


class ApplyParamPrefix(Transform):
    """Obfuscate the token name inside of a ":paramref:" reference
    to prevent Sphinx from resolving the node
    and generating a reference node that doesn't look the way we want it to.
    Ensure that our own missing-reference resolver is used.

    """

    default_priority = 210

    def apply(self):
        for ref in self.document.traverse(addnodes.pending_xref):
            # look only at paramref
            if ref["reftype"] != "paramref":
                continue

            # for params that explicitly have ".params." in the reference
            # source, let those just resolve normally.   this is not
            # really expected but it seems to work already.
            if "params." in ref["reftarget"]:
                continue

            target_tokens = ref["reftarget"].split(".")

            # apply a token to the link that will completely prevent
            # Sphinx from ever resolving this node, because WE want to
            # resolve and render the reference node, ALWAYS, THANK YOU!
            target_tokens[-1] = "_sphinx_paramlinks_" + target_tokens[-1]
            ref["reftarget"] = ".".join(target_tokens)


class LinkParams(Transform):
    # apply references targets and optional references
    # to nodes that contain our target text.
    default_priority = 210

    def apply(self):
        config_value = (
            self.document.settings.env.app.config.paramlinks_hyperlink_param
        )
        try:
            link_style = HyperlinkStyle[config_value.upper()]
        except KeyError as exc:
            raise ValueError(
                f"Unknown value {repr(config_value)} for "
                f"'paramlinks_hyperlink_param'. "
                f"Must be one of "
                f"""{
                    ', '.join(repr(member.value) for member in HyperlinkStyle)
                }."""
            ) from exc

        if link_style is HyperlinkStyle.NONE:
            return

        is_html = _is_html(self.document.settings.env.app)

        # search <strong> nodes, which will include the titles for
        # those :param: directives, looking for our special token.
        # then fix up the text within the node.
        for ref in self.document.traverse(nodes.strong):
            text = ref.astext()
            if text.startswith("_sphinx_paramlinks_"):
                components = re.match(r"_sphinx_paramlinks_(.+)\.(.+)$", text)
                location, paramname = components.group(1, 2)
                refname = _refname_from_paramname(paramname)

                refid = "%s.params.%s" % (location, refname)
                ref.parent.insert(0, nodes.target("", "", ids=[refid]))
                del ref[0]

                ref.insert(0, nodes.Text(paramname, paramname))

                if is_html:
                    # add the "p" thing only if we're the HTML builder.

                    # using a real ¶, surprising, right?
                    # http://docutils.sourceforge.net/FAQ.html
                    # #how-can-i-represent-esoteric-characters-
                    # e-g-character-entities-in-a-document

                    # "For example, say you want an em-dash (XML
                    # character entity &mdash;, Unicode character
                    # U+2014) in your document: use a real em-dash.
                    # Insert concrete characters (e.g. type a real em-
                    # dash) into your input file, using whatever
                    # encoding suits your application, and tell
                    # Docutils the input encoding. Docutils uses
                    # Unicode internally, so the em-dash character is
                    # a real em-dash internally."   OK !

                    for pos, node in enumerate(ref.parent.children):
                        # try to figure out where the node with the
                        # paramname is. thought this was simple, but
                        # readthedocs proving..it's not.
                        # TODO: need to take into account a type name
                        # with the parens.
                        if (
                            isinstance(node, nodes.TextElement)
                            and node.astext() == paramname
                        ):
                            break
                    else:
                        return

                    refparent = ref.parent

                    if link_style in (
                        HyperlinkStyle.NAME,
                        HyperlinkStyle.NAME_AND_SYMBOL,
                    ):
                        # If the parameter name should be a href, we wrap it
                        # into an <a></a> tag
                        element = refparent.pop(pos)

                        # note this is expected to be the same....
                        # assert element is ref

                        newnode = nodes.reference(
                            "",
                            "",
                            # needed to avoid recursion overflow
                            element.deepcopy(),
                            refid=refid,
                            classes=["paramname"],
                        )
                        refparent.insert(pos, newnode)

                    if link_style in (
                        HyperlinkStyle.LINK_SYMBOL,
                        HyperlinkStyle.NAME_AND_SYMBOL,
                    ):
                        # If there should be a link symbol after the parameter
                        # name, insert it here
                        refparent.insert(
                            pos + 1,
                            nodes.reference(
                                "",
                                "",
                                nodes.Text("¶", "¶"),
                                refid=refid,
                                # paramlink is our own CSS class, headerlink
                                # is theirs.  Trying to get everything we can
                                # for existing symbols...
                                classes=["paramlink", "headerlink"],
                            ),
                        )


def lookup_params(app, env, node, contnode):
    # here, we catch the "pending xref" nodes that we created with
    # the "paramref" role we added.   The resolve_xref() routine
    # knows nothing about this node type so it never finds anything;
    # the Sphinx BuildEnvironment then gives us one more chance to do a lookup
    # here.

    if node["reftype"] != "paramref":
        return None

    target = node["reftarget"]

    tokens = target.split(".")

    # if we just have :paramref:`arg` and not :paramref:`namespace.arg`,
    # we must assume that the current namespace is meant.
    if tokens == [target]:
        #
        # node.source is expected to look like:
        # /path/to/file.py:docstring of module.clsname.methname
        #
        docstring_match = re.match(r".*?:docstring of (.*)", node.source)
        if docstring_match:
            full_attr_path = docstring_match.group(1)
            fn_name = full_attr_path.split(".")[-1]
            tokens.insert(0, fn_name)

    resolve_target = ".".join(tokens[0:-1])

    # we are now cleared of Sphinx's resolver.
    # remove _sphinx_paramlinks_ token from refid so we can search
    # for the node normally.
    paramname = tokens[-1].replace("_sphinx_paramlinks_", "")

    # Remove _sphinx_paramlinks_ obfuscation string from all text nodes
    # for rendering.
    for replnode in (node, contnode):
        for text_node in replnode.traverse(nodes.Text):
            text_node.parent.replace(
                text_node,
                nodes.Text(text_node.replace("_sphinx_paramlinks_", "")),
            )

    # emulate the approach within
    # sphinx.environment.BuildEnvironment.resolve_references
    try:
        domain = env.domains[node["refdomain"]]  # hint: this will be 'py'
    except KeyError:
        return None

    # BuildEnvironment doesn't pass us "fromdocname" here as the
    # fallback, oh well
    refdoc = node.get("refdoc", None)

    # we call the same "resolve_xref" that BuildEnvironment just tried
    # to call for us, but we load the call with information we know
    # it can find, e.g. the "object" role (or we could use :meth:/:func:)
    # along with the classname/methodname/funcname minus the parameter
    # part.

    for search in ["meth", "class", "func"]:
        newnode = domain.resolve_xref(
            env, refdoc, app.builder, search, resolve_target, node, contnode
        )
        if newnode is not None:
            break

    if newnode is not None:
        # assuming we found it, tack the paramname back onto to the final
        # URI
        if "refuri" in newnode:
            newnode["refuri"] += ".params." + paramname
        elif "refid" in newnode:
            newnode["refid"] += ".params." + paramname

    return newnode


def add_stylesheet(app):
    # changed in 1.8 from add_stylesheet()
    # https://www.sphinx-doc.org/en/master/extdev/appapi.html
    # #sphinx.application.Sphinx.add_css_file
    app.add_css_file("sphinx_paramlinks.css")


def copy_stylesheet(app, exception):
    LOG.info(
        bold("The name of the builder is: %s" % app.builder.name), nonl=True
    )

    if not _is_html(app) or exception:
        return
    LOG.info(bold("Copying sphinx_paramlinks stylesheet... "), nonl=True)

    source = os.path.abspath(os.path.dirname(__file__))

    # the '_static' directory name is hardcoded in
    # sphinx.builders.html.StandaloneHTMLBuilder.copy_static_files.
    # would be nice if Sphinx could improve the API here so that we just
    # give it the path to a .css file and it does the right thing.
    dest = os.path.join(app.builder.outdir, "_static", "sphinx_paramlinks.css")
    copyfile(os.path.join(source, "sphinx_paramlinks.css"), dest)
    LOG.info("done")


def build_index(app, doctree):
    entries = _tempdata(app)

    for docname in entries:
        doc_entries = entries[docname]
        _indexentries(app.env)[docname].extend(doc_entries)

        for entry in doc_entries:
            sing, desc, ref, extra = entry[:4]
            app.env.domains["py"].data["objects"][ref] = ObjectEntry(
                docname, ref, "parameter", False
            )

    _indexentries(app.env).pop("_sphinx_paramlinks_index")


def setup(app):
    app.add_transform(LinkParams)
    app.add_transform(ApplyParamPrefix)

    # Make sure that default is are the same as in LinkParams
    # When config changes, the whole env needs to be rebuild since
    # LinkParams is applied while building the doctrees
    app.add_config_value(
        "paramlinks_hyperlink_param",
        HyperlinkStyle.LINK_SYMBOL.name,
        "env",
        [str],
    )

    # PyXRefRole is what the sphinx Python domain uses to set up
    # role nodes like "meth", "func", etc.  It produces a "pending xref"
    # sphinx node along with contextual information.
    app.add_role_to_domain("py", "paramref", PyXRefRole())

    app.connect("autodoc-process-docstring", autodoc_process_docstring)
    app.connect("builder-inited", add_stylesheet)
    app.connect("build-finished", copy_stylesheet)
    app.connect("doctree-read", build_index)
    app.connect("missing-reference", lookup_params)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
