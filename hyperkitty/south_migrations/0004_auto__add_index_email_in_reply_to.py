# -*- coding: utf-8 -*-
# pylint: skip-file
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding index on 'Email', fields ['in_reply_to']
        db.create_index(u'hyperkitty_email', ['in_reply_to'])


    def backwards(self, orm):
        # Removing index on 'Email', fields ['in_reply_to']
        db.delete_index(u'hyperkitty_email', ['in_reply_to'])


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
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'hyperkitty.attachment': {
            'Meta': {'unique_together': "((u'email', u'counter'),)", 'object_name': 'Attachment'},
            'content': ('django.db.models.fields.BinaryField', [], {}),
            'content_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'counter': ('django.db.models.fields.SmallIntegerField', [], {}),
            'email': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'attachments'", 'to': u"orm['hyperkitty.Email']"}),
            'encoding': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'size': ('django.db.models.fields.IntegerField', [], {})
        },
        u'hyperkitty.email': {
            'Meta': {'unique_together': "((u'mailinglist', u'message_id'),)", 'object_name': 'Email'},
            'archived_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'content': ('django.db.models.fields.TextField', [], {}),
            'date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_reply_to': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'mailinglist': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'emails'", 'to': u"orm['hyperkitty.MailingList']"}),
            'message_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'message_id_hash': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'children'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['hyperkitty.Email']"}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'emails'", 'to': u"orm['hyperkitty.Sender']"}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': "u'512'", 'db_index': 'True'}),
            'thread': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'emails'", 'to': u"orm['hyperkitty.Thread']"}),
            'thread_depth': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'thread_order': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'timezone': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        u'hyperkitty.favorite': {
            'Meta': {'object_name': 'Favorite'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'thread': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'favorites'", 'to': u"orm['hyperkitty.Thread']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'favorites'", 'to': u"orm['auth.User']"})
        },
        u'hyperkitty.lastview': {
            'Meta': {'object_name': 'LastView'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'thread': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'lastviews'", 'to': u"orm['hyperkitty.Thread']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'lastviews'", 'to': u"orm['auth.User']"}),
            'view_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'hyperkitty.mailinglist': {
            'Meta': {'object_name': 'MailingList'},
            'archive_policy': ('django.db.models.fields.IntegerField', [], {'default': '2'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'display_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '254', 'primary_key': 'True'}),
            'subject_prefix': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'hyperkitty.profile': {
            'Meta': {'object_name': 'Profile'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'karma': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'timezone': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '100'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "u'hyperkitty_profile'", 'unique': 'True', 'to': u"orm['auth.User']"})
        },
        u'hyperkitty.sender': {
            'Meta': {'object_name': 'Sender'},
            'address': ('django.db.models.fields.EmailField', [], {'max_length': '255', 'primary_key': 'True'}),
            'mailman_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'hyperkitty.tag': {
            'Meta': {'ordering': "[u'name']", 'object_name': 'Tag'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            'threads': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "u'tags'", 'symmetrical': 'False', 'through': u"orm['hyperkitty.Tagging']", 'to': u"orm['hyperkitty.Thread']"}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "u'tags'", 'symmetrical': 'False', 'through': u"orm['hyperkitty.Tagging']", 'to': u"orm['auth.User']"})
        },
        u'hyperkitty.tagging': {
            'Meta': {'object_name': 'Tagging'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['hyperkitty.Tag']"}),
            'thread': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['hyperkitty.Thread']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'hyperkitty.thread': {
            'Meta': {'unique_together': "((u'mailinglist', u'thread_id'),)", 'object_name': 'Thread'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'threads'", 'null': 'True', 'to': u"orm['hyperkitty.ThreadCategory']"}),
            'date_active': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mailinglist': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'threads'", 'to': u"orm['hyperkitty.MailingList']"}),
            'thread_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
        },
        u'hyperkitty.threadcategory': {
            'Meta': {'object_name': 'ThreadCategory'},
            'color': ('paintstore.fields.ColorPickerField', [], {'max_length': '7'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'})
        },
        u'hyperkitty.vote': {
            'Meta': {'unique_together': "((u'email', u'user'),)", 'object_name': 'Vote'},
            'email': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'votes'", 'to': u"orm['hyperkitty.Email']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'votes'", 'to': u"orm['auth.User']"}),
            'value': ('django.db.models.fields.SmallIntegerField', [], {'db_index': 'True'})
        }
    }

    complete_apps = ['hyperkitty']
