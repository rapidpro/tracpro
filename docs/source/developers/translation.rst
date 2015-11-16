Translation
===========

This project uses the standard `Django translation mechanisms
<https://docs.djangoproject.com/en/1.8/topics/i18n/>`_.

What goes in version control?
-----------------------------

Message files are located in the ``locale/`` directory. Files for each
available language are in subdirectories named according to ISO language codes.

The ``django.po`` file in each language directory contains all translatable
messages, plus the translation if available. Django reads translated messages
at runtime from the ``django.mo`` file, which is the compiled version of the
``.po`` file. We commit both files to GitHub for ease of tracking changes and
making reverts if needed.

Update translations
-------------------

A developer should update message files when Python or template code with
translatable messages is changed or when a new language is added. **NOTE:**
To minimize noise, we generally update translation files just once per
release cycle.

#. Create or update the message files::

    python manage.py makemessages --ignore 'conf/*' \
                                  --ignore 'docs/*' \
                                  --ignore 'requirements/*' \
                                  --no-location --no-obsolete -l en

#. Ensure that changes look reasonable using ``git diff``. E.g., if
   translations have vanished, figure out why before proceeding.

#. Edit these files to add translations, if or when able.

#. Compile the message files::

    python manage.py compilemessages

   If you get any errors due to badly formatted translations, work with your
   translators to fix the errors and start this process over.

#. Commit these changes to GitHub.

Add a new language
------------------

#. Add the language to the ``LANGUAGES`` setting.
   ``tracpro/settings/base.py``.

#. If the language is written from right to left, add the language code to
   ``RTL_LANGUAGES``.

#. Create an empty directory, named with the language's two-letter ISO code, in
   the ``locale/`` directory.

#. Update the translation files as described above.

#. Commit these changes to GitHub.
