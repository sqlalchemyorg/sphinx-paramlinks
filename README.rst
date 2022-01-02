==================
Sphinx Paramlinks
==================

A `Sphinx <http://sphinx.pocoo.org/>`_ extension which allows ``:param:``
directives within Python documentation to be linkable.

This is an experimental extension that's used by the
`SQLAlchemy <http://www.sqlalchemy.org>`_ project and related projects.

Configuration
=============

Just turn it on in ``conf.py``::

    extensions = [
                'sphinx_paramlinks',

                # your other sphinx extensions
                # ...
            ]

Since version 0.5.3, you can modify how clickable hyperlinks are placed around the names of
the parameter using the ``paramlinks_hyperlink_param`` setting in ``conf.py``::

    paramlinks_hyperlink_param='name'

This parameter accepts the following values:

* ``'none'``: No link will be be inserted. The parameter still has a target
  attached to it so that you can e.g. jump to it from the search.

* ``'name'``: The parameter name is a clickable hyperlink.

* ``'link_symbol'``: A clickable link symbol is inserted after the parameter
  name (but before an eventual type specification). By default, this symbol
  only shows when hovering the parameter description (see below)

* ``'name_and_symbol'``: link both the name and also generate a link symbol.

The default is ``paramlinks_hyperlink_param = 'link_symbol'``.

Features
========

* ``:param:`` directives within Sphinx function/method descriptions
  will be given a paragraph link so that they can be linked
  to externally.

* A new text role ``:paramref:`` is added, which works like ``:meth:``,
  ``:func:``, etc.  Just append the parameter name as an additional token::

     :paramref:`.EnvironmentContext.configure.transactional_ddl`

  The directive makes use of the existing Python role to do the method/function
  lookup, searching first the ``:meth:``, then the ``:class:``, and then  the
  ``:func:`` role; then the parameter name is applied separately to produce the
  final reference link. (new in 0.3.4, search for ``:meth:`` / ``:func:`` /
  ``:class:`` individually  rather than using ``:obj:`` which catches lots of
  things that don't have parameters)

* The paramlinks are also added to the master index as well as the list
  of domain objects, which allows them to be searchable through the
  searchindex.js system.  (new in 0.3.0)

Stylesheet
==========

The paragraph link involves a short stylesheet, to allow the links to
be visible when hovered.  This sheet is called
``sphinx_paramlinks.css`` and the plugin will copy it to the ``_static``
directory of the output automatically. The stylesheet is added to the
``css_files`` list present in the template namespace for Sphinx via the
``Sphinx.add_stylesheet()`` hook.

Customization
-------------

To customize the link styling, you can override the configuration of
``sphinx_paramlinks.css`` by adding a custom style sheet via::

     app.add_css_file("path/to/custom.css")

If the parameter name is a hyperlink, the HTML code will look something like
this::

     <a class="paramname reference internal" href="#package.method.params.parameter_name">
          <strong>parameter_name</strong>
     </a>

The class ``paramname`` is defined by ``sphinx-paramlinks`` and can be used to
customize the styling.

If a link symbol is inserted after the hyperlink, the HTML code will look
something like this::

     <a class="paramlink headerlink reference internal" href="#package.method.params.parameter_name">¶</a>

The class ``paramlink`` is defined by ``sphinx-paramlinks`` and can be used to
customize the styling.


Compatibility
=============

Python Compatibility
--------------------

sphinx-paramlinks is fully Python 3 compatible.

Sphinx Compatibility
--------------------

I've tried *very* hard to make as few assumptions as possible about Sphinx
and to use only very simple public APIs, so that architectural changes in future
Sphinx versions won't break this plugin.   To come up with this plugin I
spent many hours with Sphinx source and tried many different approaches to
various elements of functionality; hopefully what's here is as simple and
stable as possible based on the current extension capabilities of Sphinx.

One element that involves using a bit of internals is the usage of the
``sphinx.domains.python.PyXRefRole`` class, which is currently the
Sphinx class that defines roles for things like ``:meth:``,
``:func:``, etc.  The object is used as-is in order to define the
``:paramref:`` role; the product of this role is later transformed
using standard hooks.

Another assumption is that in order to locate the RST nodes Sphinx
creates for the ``:param:`` tags, we look at ``nodes.strong``,
assuming that this is the type of node currently used to render
``:param:`` within RST.  If this changes, or needs to be expanded to
support other domains, this traversal can be opened up as needed.
This part was difficult as Sphinx really doesn't provide any hooks
into how the "Info Field List" aspect of domains is handled.

Overall, the approach here is to apply extra information to constructs
going into the Sphinx system, then do some transformations as the data
comes back out.   This relies on as little of how Sphinx does its
thing as possible, rather than going with custom domains and heavy use
of injected APIs which may change in future releases.

