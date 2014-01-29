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

    // Filter
    function filter_lists() {
        var hide_by_class = {};
        $(".hide-switches input").each(function() {
            var cls = $(this).val();
            hide_by_class[cls] = $(this).prop("checked");
        });
        var filter = $.trim($(".filter-lists input").val().toLowerCase());
        $("table.lists tr.list").each(function() {
            var list_name = $.trim($(this).find("a.list-name").text());
            var list_addr = $.trim($(this).find("a.list-address").text());
            var must_hide = false;
            if (filter && list_name.indexOf(filter) === -1
                       && list_addr.indexOf(filter) === -1) {
                must_hide = true;
            }
            for (cls in hide_by_class) {
                if ($(this).hasClass(cls) && hide_by_class[cls]) {
                    must_hide = true;
                }
            }
            if (must_hide) {
                $(this).hide();
            } else {
                $(this).show();
            }
        });
    }
    $(".hide-switches input").click(filter_lists);
    $(".filter-lists input").change(function() {
        // reset status according to the "hide" checkboxes
        filter_lists();
    }).keyup(function() {
        // fire the above change event after every letter
        $(this).change();
    }).focus();

    // Initials
    $(".initials").animate({ right: 0 }, {duration: 600});
    // Override the scrolling because we have a fixed header
    $(".initials a").click(function (e) {
        e.preventDefault();
        var target = $("a[name="+$(this).attr("href").substring(1)+"]");
        $(window).scrollTop(target.offset().top - 70);
    });

    // Update list graphs
    $(".all-lists table.lists tr.list").each(function() {
        var listelem = $(this);
        var listname = $.trim(listelem.find(".list-address").text());
        url_template = url_template.replace(/@/, "%40"); // Django 1.5 compatibility, it did not escape the url tag
        var url = url_template.replace(/PLACEHOLDER%40PLACEHOLDER/, listname);
        ajax_chart(listelem.find("div.chart"), url, {height: 30});
    });
}
