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

function vote(elem, value) {
    if ($(elem).hasClass("disabled")) {
        return false;
    }
    var form = $(elem).parents("form").first();
    var data = form_to_json(form);
    data['vote'] = value;
    $.ajax({
        type: "POST",
        url: form.attr("action"),
        dataType: "json",
        data: data,
        success: function(response) {
            form.replaceWith(response.html);
        },
        error: function(jqXHR, textStatus, errorThrown) {
            alert(jqXHR.responseText);
        }
    });
    return false;
}


function setup_vote() {
    /*
    $("a.youlike").click(function(e) { e.preventDefault(); vote(this, 1); });
    $("a.youdislike").click(function(e) { e.preventDefault(); vote(this, -1); });
    */
}


/*
 * Tagging
 */

function setup_add_tag() {
    $("#add-tag-form").submit( function () {
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
 * Favorites
 */

function setup_favorites() {
    $(".favorite input[name='action']").bind("change", function() {
        // bind the links' visibilities to the hidden input status
        var form = $(this).parents("form").first();
        if ($(this).val() === "add") {
            form.find("a.saved").hide();
            form.find("a.notsaved").show();
        } else {
            form.find("a.notsaved").hide();
            form.find("a.saved").show();
        }
    }).trigger("change");
    $(".favorite a").bind("click", function(e) {
        e.preventDefault();
        if ($(this).hasClass("disabled")) {
            return;
        }
        var form = $(this).parents("form").first();
        var action_field = form.find("input[name='action']");
        var data = form_to_json(form);
        $.ajax({
            type: "POST",
            url: form.attr("action"),
            dataType: "text",
            data: data,
            success: function(response) {
                // Update the UI
                if (action_field.val() === "add") {
                    action_field.val("rm");
                } else {
                    action_field.val("add");
                }
                action_field.trigger("change");
            },
            error: function(jqXHR, textStatus, errorThrown) {
                if (jqXHR.status === 403) {
                    alert(jqXHR.responseText);
                }
            }
        });
    });
}


/*
 * Replies
 */

function setup_replies() {
    $("a.reply").click(function(e) {
        e.preventDefault();
        if (!$(this).hasClass("disabled")) {
            $(this).next().slideToggle("fast", function() {
                if ($(this).css("display") === "block") {
                    $(this).find("textarea").focus();
                }
            });
        }
    });
    $(".reply-form button[type='submit']").click(function(e) {
        e.preventDefault();
        var form = $(this).parents("form").first();
        var data = form_to_json(form);
        $.ajax({
            type: "POST",
            url: form.attr("action"),
            //dataType: "json",
            data: data,
            success: function(response) {
                form.parents(".reply-form").first().slideUp(function() {
                    form.find("textarea").val("");
                });
                $('<div class="reply-result"><div class="alert alert-success">'
                  + response + '</div></div>')
                    .appendTo(form.parents('.email-info').first())
                    .delay(2000).fadeOut('slow', function() { $(this).remove(); });
            },
            error: function(jqXHR, textStatus, errorThrown) {
                $('<div class="reply-result"><div class="alert alert-error">'
                  + '<button type="button" class="close" data-dismiss="alert">&times;</button> '
                  + jqXHR.responseText + '</div></div>')
                    .css("display", "none").insertBefore(form).slideDown();
            }
        });
    });
    $(".reply-form a.cancel").click(function(e) {
        e.preventDefault();
        $(this).parents(".reply-form").first().slideUp();
    });
    $(".reply-form a.quote").click(function(e) {
        e.preventDefault();
        var quoted = $(this).parents(".email").first()
                        .find(".email-body").clone()
                        .find(".quoted-switch").remove().end()
                        .find(".quoted-text").remove().end()
                        .text();
        var textarea = $(this).parents(".reply-form").find("textarea");
        // remove signature
        var sig_index = quoted.search(/^-- $/m);
        if (sig_index != -1) {
            quoted = quoted.substr(0, sig_index);
        }
        // add quotation marks
        quoted = $.trim(quoted).replace(/^/mg, "> ");
        // insert before any previous text
        textarea.val(quoted + "\n" + textarea.val());
        textarea.focus();
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
        .event("click", function(n) { self.location = baseurl + "/" + dates[this.index].replace(/-/g, '/') + "/"; })
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
    $(".email-info .attachments a.attachments").each(function() {
        var att_list = $(this).next("ul.attachments-list");
        var pos = $(this).position();
        att_list.css("left", pos.left);
        $(this).click(function() {
            att_list.slideToggle('fast');
        });
    });
}

function setup_quotes() {
    $('div.email-body .quoted-switch a')
        .click(function(e) {
            e.preventDefault();
            $(this).parent().next(".quoted-text").slideToggle('fast');
        });
}

function setup_months_list() {
    var current = $("#months-list li.current").parent().prev();
    if (!current.length) {
        current = false; // overview or search
    } else {
        current = current.prevAll("h3").length;
    }
    $("#months-list").accordion({ collapsible: true, active: current });
}

function setup_disabled_tooltips() {
    $("a.disabled").tooltip().click(function (e) {
        e.preventDefault();
    });
}

function setup_flash_messages() {
    $('.flashmsg').delay(3000).fadeOut('slow');
}


/*
 * General
 */

$(document).ready(function() {
    setup_vote();
    setup_attachments();
    setup_add_tag();
    setup_quotes();
    setup_months_list();
    setup_favorites();
    setup_replies();
    setup_disabled_tooltips();
    setup_flash_messages();
});
