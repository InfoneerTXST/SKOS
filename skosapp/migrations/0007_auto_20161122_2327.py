# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import skosapp.models


class Migration(migrations.Migration):

    dependencies = [
        ('skosapp', '0006_auto_20161122_2147'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rdfupload',
            name='rdf_file',
            field=models.FileField(upload_to='rdfs/', verbose_name='RDFFile'),
        ),
        migrations.AlterField(
            model_name='thesaurusupload',
            name='thesaurus_file',
            field=models.FileField(upload_to=skosapp.models.changed_filename_path, help_text="Please upload a file with a '.rj' extension.\nYou can find this in the PoolParty-exporting options of the project.", verbose_name='ThesaurusFile'),
        ),
    ]
