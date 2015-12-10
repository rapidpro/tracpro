# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0027_rename_question_text_to_name'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='question',
            options={'ordering': ('order',)},
        ),
        migrations.RenameField(
            model_name='question',
            old_name='type',
            new_name='question_type',
        ),
        migrations.AddField(
            model_name='question',
            name='rapidpro_name',
            field=models.CharField(default='', max_length=64),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='question',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='Show on TracPro'),
        ),
        migrations.AlterField(
            model_name='question',
            name='name',
            field=models.CharField(max_length=64, blank=True),
        ),
        migrations.AlterField(
            model_name='question',
            name='order',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='question',
            name='ruleset_uuid',
            field=models.CharField(max_length=36),
        ),
        migrations.AlterUniqueTogether(
            name='question',
            unique_together=set([('ruleset_uuid', 'poll')]),
        ),
    ]
