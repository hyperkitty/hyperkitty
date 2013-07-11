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
 * List descriptions on the front page
 */
function update_list_properties(url) {
    // Don't try to update them all at once, there may be hundreds of lists
    var bulksize = 5;
    // If there is still an ajaxloader, then request the properties
    var lists = $(".all-lists .mailinglist img.ajaxloader")
                    .slice(0, bulksize).parents(".mailinglist");
    if (lists.length === 0) {
        return;
    }
    var listnames = $.makeArray(lists.find(".list-address").map(
                        function() { return $(this).text(); }));
    $.ajax({
        dataType: "json",
        url: url + "?name=" + listnames.join("&name="),
        success: function(data) {
            lists.each(function() {
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
            // Request may have failed if mailman's REST server is unavailable,
            // keep going anyway.
            lists.find("img.ajaxloader").remove();
            // do it again, until all lists have been populated (or at least we
            // tried to)
            update_list_properties(url);
        }
    });
}
