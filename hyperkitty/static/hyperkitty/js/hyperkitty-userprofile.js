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
 * Last viewed threads and votes in the user's profile
 */
function update_user_profile_part(container) {
    container = $(container);
    base_url = container.attr("data-load-from");
    var loader = container.parent().find(".ajaxloader");
    function _update(url) {
        loader.show();
        $.ajax({
            url: url,
            success: function(data) {
                container.html(data);
                container.find(".pagination a").click(function(e) {
                    e.preventDefault();
                    _update(base_url + $(this).attr("href"));
                });
                // setup cancellation links
                container.find("a.cancel").click(function(e) {
                    e.preventDefault();
                    var form = $(this).parents("form").first();
                    var data = form_to_json(form);
                    $.ajax({
                        type: "POST",
                        url: form.attr("action"),
                        data: data,
                        dataType: "json",
                        success: function(response) {
                            form.parents("tr").remove();
                        },
                        error: function(jqXHR, textStatus, errorThrown) {
                            alert(jqXHR.responseText);
                        }
                    });
                });
            },
            error: function(jqXHR, textStatus, errorThrown) {
                //alert(jqXHR.responseText);
            },
            complete: function(jqXHR, textStatus) {
                loader.hide();
            }
        });
    }
    _update(base_url);
}
