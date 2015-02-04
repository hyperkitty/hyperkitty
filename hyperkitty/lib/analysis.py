# -*- coding: utf-8 -*-

# Copyright (C) 2011-2012 by the Free Software Foundation, Inc.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301,
# USA.

"""
Analysis of messages or threads of messages

Author: Aurelien Bompard <abompard@fedoraproject.org>
"""

from __future__ import absolute_import, unicode_literals

import networkx as nx


def compute_thread_order_and_depth(thread):
    graph = nx.DiGraph()
    thread_pos = {"d": 0, "o": 0} # depth, order
    def walk_successors(msgid):
        obj = graph.node[msgid]["obj"]
        obj.thread_depth = thread_pos["d"]
        obj.thread_order = thread_pos["o"]
        obj.save()
        thread_pos["d"] += 1
        thread_pos["o"] += 1
        for succ in sorted(graph.successors(msgid),
                           key=lambda m: graph.node[m]["num"]):
            walk_successors(succ)
        thread_pos["d"] -= 1
    for index, email in enumerate(thread.emails.order_by("date")):
        graph.add_node(email.id, num=index, obj=email)
        if email.parent_id is not None:
            graph.add_edge(email.parent_id, email.id)
            if not nx.is_directed_acyclic_graph(graph):
                # I don't want reply loops in my graph, thank you very much
                graph.remove_edge(email.parent_id, email.id)
    walk_successors(thread.starting_email.id)
