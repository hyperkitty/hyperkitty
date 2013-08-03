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
 * Categories
 */

function setup_category() {
    $(".thread-category form").submit(function (e) {
        e.preventDefault();
        var widget = $(this).parents(".thread-category").first();
        $.ajax({
            type: "POST",
            //dataType: "json",
            data : $(this).serialize(),
            url: $(this).attr("action"),
            success: function(data) {
                widget.html(data);
                setup_category();
            },
            error: function(jqXHR, textStatus, errorThrown) {
                // authentication and invalid data
                alert(jqXHR.responseText);
            }
        });
    });
    $(".thread-category a.label").click(function(e) {
        e.preventDefault();
        if ($(this).hasClass("disabled")) {
            return;
        }
        $(this).hide()
            .parents(".thread-category").first()
            .find("form").show();
    });
    $(".thread-category form select").change(function() {
        $(this).parents("form").first().submit();
    });
}


/*
 * Tagging
 */

function setup_tags() {
    function post_tags(e) {
        e.preventDefault();
        $.ajax({
            type: "POST",
            dataType: "json",
            data : $(this).serialize(),
            url: $(this).attr("action"),
            success: function(data) {
                $("#tags").html(data.html);
                $("#tags form").submit(post_tags);
                $("#tags form a").click(function(e) {
                    e.preventDefault();
                    $(this).parents("form").first().submit();
                });
                $(this).find("#id_tag").value("");
            },
            error: function(jqXHR, textStatus, errorThrown) {
                // authentication and invalid data
                alert(jqXHR.responseText);
            }
        });
    }
    $("#add-tag-form").submit(post_tags);
    $("#tags form").submit(post_tags);
    $("#tags form a").click(function(e) {
        e.preventDefault();
        $(this).parents("form").first().submit();
    });
    // Autocomplete
    $("#id_tag").autocomplete({
        //minLength: 2,
        source: $("#add-tag-form").attr("data-autocompleteurl")
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

function setup_unreadnavbar(element) {
    element = $(element);
    if (element.length === 0) {
        return;
    }
    var current_index;
    function scroll(inc) {
        var unreads = $(".email.unread");
        if (unreads.length == 0) { return; }
        if (typeof current_index == "undefined") {
            if (inc == 1) { current_index = -1; }
            if (inc == -1) { current_index = unreads.length; }
        }
        current_index = current_index + inc;
        if (current_index < 0) { current_index = unreads.length - 1; }
        if (current_index >= unreads.length) { current_index = 0; }
        element.find(".unreadindex").text(current_index + 1);
        // compensate for the fixed banner at the top
        var target = unreads.eq(current_index).offset().top - 70;
        $("html,body").stop(true, false).animate({
            scrollTop: target
        }, 500);
    }
    element.find(".nextunread").click(function(e) { e.preventDefault(); scroll(1); });
    element.find(".prevunread").click(function(e) { e.preventDefault(); scroll(-1); });
    $(document).bind("keydown", "j", function(e) { scroll(1); });
    $(document).bind("keydown", "k", function(e) { scroll(-1); });
    element.find("a").tooltip();
    element.animate({height: "show"}, 700);
}



/*
 * Thread replies list
 * Updates the list of replies in a thread chunk-by-chunk to avoid blocking the
 * UI
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
                setup_attachments(newcontent);
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
 * Re-attach threads
 */
function setup_reattach() {
    $(".reattach-thread li.manual input[type='text']").focus( function() {
        $(this).parents("li").first()
            .find("input[type='radio']")
            .prop("checked", true);
    });
    $(".reattach-thread form.search").submit(function (e) {
        e.preventDefault();
        var results_elem = $(this).parent().find("ul.suggestions");
        var url = $(this).attr("action") + "?" + $(this).serialize();
        results_elem.find("img.ajaxloader").show();
        $.ajax({
            url: url,
            success: function(data) {
                results_elem.html(data);
            },
            error: function(jqXHR, textStatus, errorThrown) {
                alert(jqXHR.responseText);
            },
            complete: function(jqXHR, textStatus) {
                results_elem.find("img.ajaxloader").hide();
            }
        });
    }).submit();
}
