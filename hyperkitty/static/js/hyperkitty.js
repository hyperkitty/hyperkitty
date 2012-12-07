/*
 * -*- coding: utf-8 -*-
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
        data: data,
        success: function(response) {
            // @TODO : Remove this reload and update the count using the AJAX response
            location.reload();
        },
        error: function(jqXHR, textStatus, errorThrown) {
            // You must be authenticated to do that
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
            data : $(this).serialize(),
            url: $(this).attr("action"),
            success: function(data){
                // @TODO : Remove this reload and update the tag list using the AJAX response
                //location.reload();
            },
            error: function(jqXHR, textStatus, errorThrown) {
                // You must be authenticated to do that
                if (jqXHR.status === 403) {
                    alert(jqXHR.responseText);
                }
            }
        });
        return false;
    });
}



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
