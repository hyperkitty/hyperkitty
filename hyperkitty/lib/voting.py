#-*- coding: utf-8 -*-
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
# Author: Aurelien Bompard <abompard@fedoraproject.org>
#


from hyperkitty.models import Rating


def get_votes(message_id_hash, user=None):
    """Extract all the votes for this message"""
    likes = dislikes = 0
    try:
        votes = Rating.objects.filter(messageid=message_id_hash)
    except Rating.DoesNotExist:
        votes = {}
    myvote = 0
    for vote in votes:
        if vote.vote == 1:
            likes += 1
        elif vote.vote == -1:
            dislikes += 1
        if user is not None and user.is_authenticated() and vote.user == user:
            myvote = vote.vote
    return likes, dislikes, myvote


def set_message_votes(message, user=None):
    # Extract all the votes for this message
    message.likes, message.dislikes, message.myvote = \
            get_votes(message.message_id_hash, user)
    message.likestatus = "neutral"
    if message.likes - message.dislikes >= 10:
        message.likestatus = "likealot"
    elif message.likes - message.dislikes > 0:
        message.likestatus = "like"
    #elif message.likes - message.dislikes < 0:
    #    message.likestatus = "dislike"
