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
 * Generic
 */
function form_to_json(form) {
    var form_data = form.serializeArray();
    var data = {};
    for (input in form_data) {
        data[form_data[input].name] = form_data[input].value;
    }
    return data;
}


/*
 * Voting
 */

function vote(elem) {
    if ($(elem).hasClass("disabled")) {
        return;
    }
    var value = parseInt($(elem).attr("data-vote"));
    var form = $(elem).parents("form").first();
    var data = form_to_json(form);
    data['vote'] = value;
    $.ajax({
        type: "POST",
        url: form.attr("action"),
        dataType: "json",
        data: data,
        success: function(response) {
            var newcontent = $(response.html);
            form.replaceWith(newcontent);
            setup_vote(newcontent); // re-bind events
        },
        error: function(jqXHR, textStatus, errorThrown) {
            alert(jqXHR.responseText);
        }
    });
}


function setup_vote(baseElem) {
    if (!baseElem) {
        baseElem = document;
    }
    $(baseElem).find("a.vote").click(function(e) {
        e.preventDefault();
        vote(this);
    });
}


/*
 * Misc.
 */

function setup_months_list() {
    var current = $("#months-list li.current").parent().prev();
    if (!current.length) {
        current = 0; // overview or search
    } else {
        current = current.prevAll("h3").length;
    }
    $("#months-list").accordion({ collapsible: true, active: current });
}

function setup_disabled_tooltips(baseElem) {
    if (!baseElem) {
        baseElem = document;
    }
    $(baseElem).find("a.disabled").tooltip().click(function (e) {
        e.preventDefault();
    });
}

function setup_flash_messages() {
    $('.flashmsgs .alert-success').delay(3000).fadeOut('slow');
}


/*
 * Activate
 */

$(document).ready(function() {
    setup_vote();
    setup_months_list();
    setup_disabled_tooltips();
    setup_flash_messages();
});
