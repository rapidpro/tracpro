Localization
=============================

If you are new to Django you can read about the Django approach to localization used by TracPro at `http://www.djangobook.com/en/2.0/chapter19.html <http://www.djangobook.com/en/2.0/chapter19.html>`_.

Adding New Languages
---------------------

To add a new language to TracPro:

#. Edit `settings/base.py <https://github.com/rapidpro/tracpro/blob/develop/tracpro/settings/base.py>`_ and add the language to the `LANGUAGES` list setting.
#. If the language is RTL, add its code to `RTL_LANGUAGES`.
#. Create an empty directory under the [locale](https://github.com/rapidpro/tracpro/tree/master/locale) folder using the 2-letter ISO code of the language as the folder name. TODO: locale info

Translating
------------------

To generate new *.po files run the following command::

    $./manage.py makemessages --all --ignore=*/compressor/* --ignore=*/sorl/* --ignore=*/xlwt/*

TracPro currently uses `Transifex <https://www.transifex.com/projects/p/tracpro/>`_ for translation. The English *.po file is uploaded there and translators can provide translations of the various strings used in the application. We can then download *.po files in different languages.

When Django is running, it fetches localized messages from *.mo files. We can generate these from the *.po files as follows::

    ./manage.py compilemessages
