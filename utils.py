# -*- coding: utf-8 -*-
# Copyright (C) 1998-2012 by the Free Software Foundation, Inc.
#
# This file is part of HyperKitty.
#
# HyperKitty is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# HyperKitty is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# HyperKitty.  If not, see <http://www.gnu.org/licenses/>.
#
# Author: Aamir Khan <syst3m.w0rm@gmail.com>
# 

import logging
import traceback

from django.conf import settings
from django.core import mail
from django.views.debug import ExceptionReporter, get_exception_reporter_filter

LOG_FILE = 'hk.log'

def log(level, *args, **kwargs):
    """Small wrapper around logger functions."""
    {
     'debug': logger.debug,
     'error': logger.error,
     'exception': logger.exception,
     'warn': logger.warn
    }[level](*args, **kwargs)


class HyperKittyLogHandler(logging.Handler):
    """A custom HyperKitty log handler.

    If the request is passed as the first argument to the log record,
    request data will be provided in the email report.
    """

    def __init__(self, log_to_file=True, email_admins=True):
        logging.Handler.__init__(self)
        self.log_to_file = log_to_file
	self.email_admins = email_admins

    def emit(self, record):
        try:
            request = record.request
            subject = '%s (%s IP): %s' % (
                record.levelname,
                (request.META.get('REMOTE_ADDR') in settings.INTERNAL_IPS
                 and 'internal' or 'EXTERNAL'),
                record.getMessage()
            )
            filter = get_exception_reporter_filter(request)
            request_repr = filter.get_request_repr(request)
        except Exception:
            subject = '%s: %s' % (
                record.levelname,
                record.getMessage()
            )
            request = None
            request_repr = "Request repr() unavailable."
        subject = self.format_subject(subject)

        if record.exc_info:
            exc_info = record.exc_info
            stack_trace = '\n'.join(traceback.format_exception(*record.exc_info))
        else:
            exc_info = (None, record.getMessage(), None)
            stack_trace = 'No stack trace available'

        message = "%s\n\n%s" % (stack_trace, request_repr)
        reporter = ExceptionReporter(request, is_email=True, *exc_info)
        html_message = reporter.get_traceback_html()

	if self.email_admins:
		mail.mail_admins(subject, message, fail_silently=True, html_message=html_message)	

	if self.log_to_file:
		log_file = open(LOG_FILE, 'a')
		log_file.write(message)
		log_file.close()

    def format_subject(self, subject):
        """
        Escape CR and LF characters, and limit length.
        RFC 2822's hard limit is 998 characters per line. So, minus "Subject: "
        the actual subject must be no longer than 989 characters.
        """
        formatted_subject = subject.replace('\n', '\\n').replace('\r', '\\r')
        return formatted_subject[:989]


logger = None
if not logger:
    logger = logging.getLogger('HyperKitty')

if not logger.handlers:
    logger.addHandler(HyperKittyLogHandler(True, True))
