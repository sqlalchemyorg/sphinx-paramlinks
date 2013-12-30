============
Autodoc Mods
============

A `Sphinx <http://sphinx.pocoo.org/>`_ extension which enhances the display
of autodoc directives.

This is an experimental, possibly-not-useful extension that's used by the
`SQLAlchemy <http://www.sqlalchemy.org>`_ project and related projects.

Configuration
=============

autodoc_links does it's thing without any special configuration by default,
just turn it on in ``conf.py``::

    extensions = [
                # autodoc extension
                'autodoc_links',

                # your other sphinx extensions
                # ...
            ]

The class documentation feature accepts a translation mapping of module names
that can display module names differently than they are actually indexed::

    autodoc_links_convert_modname = {
        "sqlalchemy.sql.sqltypes": "sqlalchemy.types",
        "sqlalchemy.sql.type_api": "sqlalchemy.types",
        "sqlalchemy.sql.schema": "sqlalchemy.schema",
        "sqlalchemy.sql.elements": "sqlalchemy.sql.expression",
        "sqlalchemy.sql.selectable": "sqlalchemy.sql.expression",
        "sqlalchemy.sql.dml": "sqlalchemy.sql.expression",
        "sqlalchemy.sql.ddl": "sqlalchemy.schema",
        "sqlalchemy.sql.base": "sqlalchemy.sql.expression",
        ("sqlalchemy.engine.interfaces", "Connectable"): "sqlalchemy.engine"
    }

Features
========

* ``:param:`` directives will be given a paragraph link so that they can be linked
   to externally.

* TODO: a new directive ``:param:`` will allow these links to be indicated
  in source.

* The "bases" of a class are rendered using the "autodoc_links_convert_modname"
   translation map for the module name.

* When a class is autodoc'ed with ``inherited-members``, the display of those
  inherited members is augmented with a linked indicator
  "inherited from the X <attribute|method> of the <classname> class".  This provides
  some sanity to the large number of repeated methods and attributes one gets
  when using the ``inherited-members`` directive.

