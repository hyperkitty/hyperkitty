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
                alert(jqXHR.responseText);
            }
        });
    });
}


/*
 * Replies
 */

function setup_emails_list(baseElem) {
    if (!baseElem) {
        baseElem = document;
    }
    // Attachements
    $(baseElem).find(".email-info .attachments a.attachments").each(function() {
        var att_list = $(this).next("ul.attachments-list");
        var pos = $(this).position();
        att_list.css("left", pos.left);
        $(this).click(function() {
            att_list.slideToggle('fast');
        });
    });
    // Quotes
    $(baseElem).find('div.email-body .quoted-switch a')
        .click(function(e) {
            e.preventDefault();
            $(this).parent().next(".quoted-text").slideToggle('fast');
        });
    setup_replies(baseElem);
}

function fold_quotes(baseElem) {
    $(baseElem).find('div.email-body .quoted-text').each(function() {
        var linescount = $(this).text().split("\n").length;
        if (linescount > 3) {
            // hide if the quote is more than 3 lines long
            $(this).hide();
        }
    });
}

function setup_replies(baseElem) {
    if (!baseElem) {
        baseElem = document;
    }
    $(baseElem).find("a.reply").click(function(e) {
        e.preventDefault();
        if (!$(this).hasClass("disabled")) {
            $(this).next().slideToggle("fast", function() {
                if ($(this).css("display") === "block") {
                    $(this).find("textarea").focus();
                }
            });
        }
    });
    $(baseElem).find(".reply-form button[type='submit']").click(function(e) {
        e.preventDefault();
        var form = $(this).parents("form").first();
        // remove previous error messages
        form.find("div.reply-result").remove();
        var data = form_to_json(form);
        $.ajax({
            type: "POST",
            url: form.attr("action"),
            dataType: "json",
            data: data,
            success: function(response) {
                var reply = $(response.message_html);
                reply.insertAfter(form.parents(".email").first().parent());
                form.parents(".reply-form").first().slideUp(function() {
                    form.find("textarea").val("");
                    reply.slideDown();
                });
                $('<div class="reply-result"><div class="alert alert-success">'
                  + response.result + '</div></div>')
                    .appendTo(form.parents('.email-info').first())
                    .delay(2000).fadeOut('slow', function() { $(this).remove(); });
            },
            error: function(jqXHR, textStatus, errorThrown) {
                $('<div class="reply-result"><div class="alert alert-error">'
                  + '<button type="button" class="close" data-dismiss="alert">&times;</button> '
                  + jqXHR.responseText + '</div></div>')
                    .css("display", "none").prependTo(form).slideDown();
            }
        });
    });
    $(baseElem).find(".reply-form a.cancel").click(function(e) {
        e.preventDefault();
        $(this).parents(".reply-form").first().slideUp();
    });
    $(baseElem).find(".reply-form a.quote").click(function(e) {
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
    function set_new_thread(checkbox) {
        var this_form = checkbox.parents("form").first();
        var subj = this_form.find("input[name='subject']").parents("p").first();
        if (checkbox.is(":checked")) {
            subj.slideDown("fast");
            subj.find("input").focus();
        } else {
            subj.slideUp("fast");
            this_form.find("textarea").focus();
        }
    }
    $(baseElem).find(".reply-form input[name='newthread']").change(function() {
        set_new_thread($(this));
    }).change();
}


/*
 * Recent activity graph
 */
function activity_graph(elem_id, dates, counts, baseurl) {
    function merge(dates, counts) {
        result = []
        for(i = 0; i < dates.length; i++) {
            result.push({
                "date": dates[i],
                "count": counts[i]
            })
        }
        return result;
    }
    var data = merge(dates, counts);
    var margin = {top: 20, right: 20, bottom: 100, left: 50},
        width = 540 - margin.left - margin.right,
        height = 330 - margin.top - margin.bottom;

    var format_in = d3.time.format("%Y-%m-%d");
    var format_out = d3.time.format("%m-%d");

    var x = d3.time.scale()
        .range([0, width]);

    var y = d3.scale.linear()
        .range([height, 0]);

    var xAxis = d3.svg.axis()
        .scale(x)
        .orient("bottom")
        .tickFormat(format_out)
        .ticks(d3.time.days, 2);

    var yAxis = d3.svg.axis()
        .scale(y)
        .orient("left")
        .ticks(5)
        .tickSubdivide(1);

    var area = d3.svg.area()
        .x(function(d) { return x(d.date); })
        .y0(height)
        .y1(function(d) { return y(d.count); });

    var svg = d3.select(elem_id).append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
      .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    data.forEach(function(d) {
        d.date = format_in.parse(d.date);
        d.count = parseInt(d.count);
    });

    x.domain(d3.extent(data, function(d) { return d.date; }));
    y.domain([0, d3.max(data, function(d) { return d.count; })]);

    svg.append("path")
      .datum(data)
      .attr("class", "area")
      .attr("d", area);

    svg.append("g")
      .attr("class", "x axis")
      .attr("transform", "translate(0," + height + ")")
      .call(xAxis)
      .selectAll("text")
        .attr("y", -5)
        .attr("x", -30)
        .attr("transform", function(d) {
            return "rotate(-90)"
            });

    svg.append("g")
      .attr("class", "y axis")
      .call(yAxis)
    .append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 6)
      .attr("dy", ".71em")
      .style("text-anchor", "end")
      .text("Messages");
}


/*
 * Thread replies list
 */
function update_thread_replies(url) {
    function load_more(current_url) {
        $.ajax({
            dataType: "json",
            url: current_url,
            success: function(data) {
                // replies
                var newcontent = $(data.replies_html);
                $(".replies").append(newcontent)
                             .append($(".replies .ajaxloader"));
                // re-bind events
                setup_emails_list(newcontent);
                fold_quotes(newcontent);
                setup_disabled_tooltips(newcontent);
                setup_vote(newcontent);
                // load the rest if applicable
                if (data.more_pending) {
                    load_more(url+"&offset="+data.next_offset);
                } else {
                    $(".replies .ajaxloader").remove();
                }
            },
            error: function(jqXHR, textStatus, errorThrown) {
                if (jqXHR.responseText !== "") {
                    alert(jqXHR.responseText);
                }
            }
        });
    }
    load_more(url);
}


/*
 * List descriptions on the front page
 */
function update_list_properties(url) {
    $.ajax({
        dataType: "json",
        url: url,
        success: function(data) {
            $(".all-lists .mailinglist").each(function() {
                var name = $(this).find(".list-address").text();
                if (!data[name]) {
                    return;
                }
                if (data[name]["display_name"]) {
                    $(this).find(".list-name").text(data[name]["display_name"]);
                }
                if (data[name]["description"]) {
                    $(this).find(".list-description")
                           .text(data[name]["description"]);
                }
            });
        },
        error: function(jqXHR, textStatus, errorThrown) {
            //alert(jqXHR.responseText);
        },
        complete: function(jqXHR, textStatus) {
            $(".all-lists .mailinglist img.ajaxloader").remove();
        }
    });
}


/*
 * Misc.
 */

function setup_months_list() {
    var current = $("#months-list li.current").parent().prev();
    if (!current.length) {
        current = false; // overview or search
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
 * General
 */

$(document).ready(function() {
    setup_vote();
    setup_add_tag();
    setup_months_list();
    setup_favorites();
    setup_emails_list();
    setup_disabled_tooltips();
    setup_flash_messages();
});
