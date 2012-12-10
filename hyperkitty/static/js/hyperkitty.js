/*
 * Copyright (C) 1998-2012 by the Free Software Foundation, Inc.
 *
 * This file is part of HyperKitty.
 *
 * HyperKitty is free software: you can redistribute it and/or modify it under
 * the terms of the GNU General Public License as published by the Free
 * Software Foundation, either version 3 of the License, or (at your option)
 * any later version.
 *
 * HyperKitty is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
 * more details.
 *
 * You should have received a copy of the GNU General Public License along with
 * HyperKitty.  If not, see <http://www.gnu.org/licenses/>.
 *
 * Author: Aurelien Bompard <abompard@fedoraproject.org>
 */



/*
 * Voting
 */

function vote(elem, value) {
    var form_data = $(elem).parent("form").serializeArray();
    var data = {};
    for (input in form_data) {
        data[form_data[input].name] = form_data[input].value;
    }
    data['vote'] = value;
    $.ajax({
        type: "POST",
        url: $(elem).parent("form").attr("action"),
        dataType: "json",
        data: data,
        success: function(response) {
            var likestatus = $(elem).parent("form").find(".likestatus");
            likestatus.find(".likecount").html(response.like);
            likestatus.find(".dislikecount").html(response.dislike);
        },
        error: function(jqXHR, textStatus, errorThrown) {
            // authentication or double-vote
            if (jqXHR.status === 403) {
                alert(jqXHR.responseText);
            }
        }
    });
}


function setup_vote() {
    $(".voteup").click(function() { vote(this, 1); return false; });
    $(".votedown").click(function() { vote(this, -1); return false; });
}


/*
 * Tagging
 */

function setup_add_tag() {
    $("#add_tag_form").submit( function () {
        $.ajax({
            type: "POST",
            dataType: "json",
            data : $(this).serialize(),
            url: $(this).attr("action"),
            success: function(data) {
                $("#tags").html(data.html);
            },
            error: function(jqXHR, textStatus, errorThrown) {
                // authentication and invalid data
                alert(jqXHR.responseText);
            }
        });
        return false;
    });
}


/*
 * Recent activity graph
 */

function activity_graph(dates, data, baseurl) {
    var w = 500,
        h = 300,
        x = pv.Scale.ordinal(pv.range(32)).splitBanded(0, w, 4/5),
        y = pv.Scale.linear(0, Math.max.apply(null, data)+1).range(0, h);

    var vis = new pv.Panel()
        .width(w)
        .height(250)
        .bottom(60)
        .left(30)
        .right(5)
        .top(5);

    var bar = vis.add(pv.Bar)
        .data(data)
        .event("click", function(n) self.location = baseurl + dates[this.index] + "/")
        .left(function() x(this.index))
        .width(x.range().band)
        .bottom(0)
        .height(y);

    bar.anchor("bottom").add(pv.Label)
        .textMargin(5)
        .textAlign("right")
        .textBaseline("middle")
        .textAngle(-Math.PI / 3)
        .text(function() xlabel(this.index));

    function xlabel(ind) {
        if (!dates[ind -1]) {
            return dates[ind];
        }
        prev = dates[ind - 1];
        cur = dates[ind];
        if (prev.substring(0,7) == cur.substring(0,7)) {
            cur = cur.substring(8);
        }
        return cur;
    }

    vis.add(pv.Rule)
        .data(y.ticks())
        .bottom(function(d) Math.round(y(d)) - .5)
        .strokeStyle(function(d) d ? "rgba(255,255,255,.3)" : "#000")
        .add(pv.Rule)
        .left(0)
        .width(5)
        .strokeStyle("#000")
        .anchor("left").add(pv.Label)
        .text(function(d) d.toFixed(1));

    vis.render();
}


/*
 * Misc.
 */

function setup_attachments() {
    $("ul.email_info li.attachments ul.attachments-list").hide();
    $("ul.email_info li.attachments > a").click(function() {
        $(this).next("ul").fadeToggle('fast');
    });
}



/*
 * General
 */

$(document).ready(function() {
    setup_vote();
    setup_attachments();
    setup_add_tag();
});
