/*
 * Copyright (C) 2012-2013 by the Free Software Foundation, Inc.
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



function setup_index(url_template) {
    $("table.lists tr.list").click(function(e) {
        document.location.href = $(this).find("a.list-name").attr("href");
    });

    // Helper to load the graph
    function show_ajax_chart(listelem) {
        if (!listelem.is(":visible")) {
            return;
        }
        var listname = $.trim(listelem.find(".list-address").text());
        url_template = url_template.replace(/@/, "%40"); // Django 1.5 compatibility, it did not escape the url tag
        var url = url_template.replace(/PLACEHOLDER%40PLACEHOLDER/, listname);
        ajax_chart(listelem.find("div.chart"), url, {height: 30});
    }

    // Filter
    function filter_lists() {
        var hide_by_class = {};
        $(".hide-switches input").each(function() {
            var cls = $(this).val();
            hide_by_class[cls] = $(this).prop("checked");
        });
        var filter = null;
        if ($(".filter-lists input[type=text]").length !== 0) {
            // The field does not exist if there are only a few lists
            filter = $.trim($(".filter-lists input[type=text]").val().toLowerCase());
        }
        $("table.lists tr.list").each(function() {
            var list_name = $.trim($(this).find("a.list-name").text());
            var list_addr = $.trim($(this).find("a.list-address").text());
            var must_hide = false;
            // name filter
            if (filter && list_name.indexOf(filter) === -1
                       && list_addr.indexOf(filter) === -1) {
                must_hide = true;
            }
            // class filter
            for (cls in hide_by_class) {
                if ($(this).hasClass(cls) && hide_by_class[cls]) {
                    must_hide = true;
                }
            }
            // now apply the filters
            if (must_hide) {
                $(this).hide();
            } else {
                $(this).show();
                show_ajax_chart($(this));
            }
        });
    }
    $(".hide-switches input").click(filter_lists);
    var _filter_timeout = null;
    $(".filter-lists input").change(function() {
        clearTimeout(_filter_timeout)
        // reset status according to the "hide" checkboxes
        window.setTimeout(filter_lists, 500);
    }).keyup(function() {
        // fire the above change event after every letter
        $(this).change();
    }).focus();
    filter_lists(); // Filter on page load

    // Back to top link
    setup_back_to_top_link(220); // set offset to 220 for link to appear

    // Update list graphs for visible lists
    $(".all-lists table.lists tr.list:visible").each(function() {
        show_ajax_chart($(this));
    });
}
