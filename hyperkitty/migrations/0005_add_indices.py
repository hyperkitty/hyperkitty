# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding index on 'Favorite', fields ['list_address']
        db.create_index(u'hyperkitty_favorite', ['list_address'])

        # Adding index on 'Favorite', fields ['threadid']
        db.create_index(u'hyperkitty_favorite', ['threadid'])

        # Adding index on 'Tag', fields ['list_address']
        db.create_index(u'hyperkitty_tag', ['list_address'])

        # Adding index on 'Tag', fields ['threadid']
        db.create_index(u'hyperkitty_tag', ['threadid'])

        # Adding index on 'Rating', fields ['list_address']
        db.create_index(u'hyperkitty_rating', ['list_address'])

        # Adding index on 'Rating', fields ['messageid']
        db.create_index(u'hyperkitty_rating', ['messageid'])

        # Adding index on 'LastView', fields ['list_address']
        db.create_index(u'hyperkitty_lastview', ['list_address'])

        # Adding index on 'LastView', fields ['threadid']
        db.create_index(u'hyperkitty_lastview', ['threadid'])


    def backwards(self, orm):
        # Removing index on 'LastView', fields ['threadid']
        db.delete_index(u'hyperkitty_lastview', ['threadid'])

        # Removing index on 'LastView', fields ['list_address']
        db.delete_index(u'hyperkitty_lastview', ['list_address'])

        # Removing index on 'Rating', fields ['messageid']
        db.delete_index(u'hyperkitty_rating', ['messageid'])

        # Removing index on 'Rating', fields ['list_address']
        db.delete_index(u'hyperkitty_rating', ['list_address'])

        # Removing index on 'Tag', fields ['threadid']
        db.delete_index(u'hyperkitty_tag', ['threadid'])

        # Removing index on 'Tag', fields ['list_address']
        db.delete_index(u'hyperkitty_tag', ['list_address'])

        # Removing index on 'Favorite', fields ['threadid']
        db.delete_index(u'hyperkitty_favorite', ['threadid'])

        # Removing index on 'Favorite', fields ['list_address']
        db.delete_index(u'hyperkitty_favorite', ['list_address'])


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'hyperkitty.favorite': {
            'Meta': {'object_name': 'Favorite'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'list_address': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'threadid': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'hyperkitty.lastview': {
            'Meta': {'object_name': 'LastView'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'list_address': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'threadid': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'view_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'hyperkitty.rating': {
            'Meta': {'object_name': 'Rating'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'list_address': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'messageid': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'vote': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        u'hyperkitty.tag': {
            'Meta': {'object_name': 'Tag'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'list_address': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'tag': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'threadid': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'})
        },
        u'hyperkitty.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'karma': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.User']", 'unique': 'True'})
        }
    }

    complete_apps = ['hyperkitty']