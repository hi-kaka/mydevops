# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('detail', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupInfo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('group_name', models.CharField(max_length=80, verbose_name='\u7ec4\u540d')),
                ('group_detail', models.CharField(default=b'', max_length=256, null=True, verbose_name='\u7ec4\u4fe1\u606f\u63cf\u8ff0')),
            ],
            options={
                'db_table': 'groupinfo',
                'verbose_name': 'Ansible\u81ea\u52a8\u5316\u4efb\u52a1\u5206\u7ec4\u4fe1\u606f\u8868',
                'verbose_name_plural': 'Ansible\u81ea\u52a8\u5316\u4efb\u52a1\u5206\u7ec4\u4fe1\u606f\u8868',
            },
        ),
        migrations.AlterField(
            model_name='statisticsrecord',
            name='datatime',
            field=models.DateTimeField(default=b'2019-01-06', verbose_name='\u66f4\u65b0\u65f6\u95f4'),
        ),
        migrations.AddField(
            model_name='connectioninfo',
            name='conn_grp1',
            field=models.ForeignKey(related_name='conn_grp1', verbose_name='\u7ec4\u4e00\u5916\u952e\u540d', to='detail.GroupInfo', null=True),
        ),
        migrations.AddField(
            model_name='connectioninfo',
            name='conn_grp10',
            field=models.ForeignKey(related_name='conn_grp10', verbose_name='\u7ec4\u5341\u5916\u952e\u540d', to='detail.GroupInfo', null=True),
        ),
        migrations.AddField(
            model_name='connectioninfo',
            name='conn_grp2',
            field=models.ForeignKey(related_name='conn_grp2', verbose_name='\u7ec4\u4e8c\u5916\u952e\u540d', to='detail.GroupInfo', null=True),
        ),
        migrations.AddField(
            model_name='connectioninfo',
            name='conn_grp3',
            field=models.ForeignKey(related_name='conn_grp3', verbose_name='\u7ec4\u4e09\u5916\u952e\u540d', to='detail.GroupInfo', null=True),
        ),
        migrations.AddField(
            model_name='connectioninfo',
            name='conn_grp4',
            field=models.ForeignKey(related_name='conn_grp4', verbose_name='\u7ec4\u56db\u5916\u952e\u540d', to='detail.GroupInfo', null=True),
        ),
        migrations.AddField(
            model_name='connectioninfo',
            name='conn_grp5',
            field=models.ForeignKey(related_name='conn_grp5', verbose_name='\u7ec4\u4e94\u5916\u952e\u540d', to='detail.GroupInfo', null=True),
        ),
        migrations.AddField(
            model_name='connectioninfo',
            name='conn_grp6',
            field=models.ForeignKey(related_name='conn_grp6', verbose_name='\u7ec4\u516d\u5916\u952e\u540d', to='detail.GroupInfo', null=True),
        ),
        migrations.AddField(
            model_name='connectioninfo',
            name='conn_grp7',
            field=models.ForeignKey(related_name='conn_grp7', verbose_name='\u7ec4\u4e03\u5916\u952e\u540d', to='detail.GroupInfo', null=True),
        ),
        migrations.AddField(
            model_name='connectioninfo',
            name='conn_grp8',
            field=models.ForeignKey(related_name='conn_grp8', verbose_name='\u7ec4\u516b\u5916\u952e\u540d', to='detail.GroupInfo', null=True),
        ),
        migrations.AddField(
            model_name='connectioninfo',
            name='conn_grp9',
            field=models.ForeignKey(related_name='conn_grp9', verbose_name='\u7ec4\u4e5d\u5916\u952e\u540d', to='detail.GroupInfo', null=True),
        ),
    ]
