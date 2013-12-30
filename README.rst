==================
Sphinx Paramlinks
==================

A `Sphinx <http://sphinx.pocoo.org/>`_ extension which allows ``:param:``
directives within Python documentation to be linkable.

This is an experimental, possibly-not-useful extension that's used by the
`SQLAlchemy <http://www.sqlalchemy.org>`_ project and related projects.

Configuration
=============

Just turn it on in ``conf.py``::

    extensions = [
                'sphinx_paramlinks',

                # your other sphinx extensions
                # ...
            ]


Features
========

* ``:param:`` directives will be given a paragraph link so that they can be linked
   to externally.

* TODO: a new directive ``:param:`` will allow these links to be indicated
  in source.

