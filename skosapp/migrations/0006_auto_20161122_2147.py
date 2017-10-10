# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import skosapp.models


class Migration(migrations.Migration):

    dependencies = [
        ('skosapp', '0005_thesaurusupload'),
    ]

    operations = [
        migrations.AlterField(
            model_name='thesaurusupload',
            name='thesaurus_file',
            field=models.FileField(help_text="Please upload a file with a '.rj' extension.\nYou can find this in the PoolParty-exporting options of the project.", upload_to=skosapp.models.changed_filename_path, verbose_name='File'),
        ),
    ]
