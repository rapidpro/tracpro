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
        migrations.AlterField(
            model_name='question',
            name='question_type',
            field=models.CharField(max_length=1, verbose_name='question type', choices=[('O', 'Open Ended'), ('C', 'Multiple Choice'), ('N', 'Numeric'), ('M', 'Menu'), ('K', 'Keypad'), ('R', 'Recording')]),
        ),
        migrations.AddField(
            model_name='question',
            name='rapidpro_name',
            field=models.CharField(default='', max_length=64, verbose_name='RapidPro name'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='question',
            name='poll',
            field=models.ForeignKey(related_name='questions', verbose_name='poll', to='polls.Poll'),
        ),
        migrations.AlterField(
            model_name='question',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='show on TracPro'),
        ),
        migrations.AlterField(
            model_name='question',
            name='name',
            field=models.CharField(max_length=64, verbose_name='name', blank=True),
        ),
        migrations.AlterField(
            model_name='question',
            name='order',
            field=models.IntegerField(default=0, verbose_name='order'),
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
