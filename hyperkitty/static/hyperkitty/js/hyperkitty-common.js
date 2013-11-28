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
 * New messages (or replies)
 */

function setup_attachments(baseElem) {
    if (!baseElem) {
        baseElem = document;
    }
    function add_attach_form (e) {
        e.preventDefault();
        var form = $(this).parents("form").first();
        form.find(".attach-files-template")
            .clone().removeClass("attach-files-template")
            .appendTo(form.find(".attach-files"));
        form.find(".attach-files span a").click(function (e) {
            e.preventDefault();
            $(this).parent().remove();
            if (form.find(".attach-files input").length === 0) {
                form.find(".attach-files-add").hide();
                form.find(".attach-files-first").show();
            };
        });
        form.find(".attach-files-first").hide();
        form.find(".attach-files-add").show();
    }
    $(baseElem).find(".attach-files-add").click(add_attach_form);
    $(baseElem).find(".attach-files-first").click(add_attach_form);
}



/*
 * Recent activity bar chart
 */

function chart(elem_id, data, default_props) {
    /* Function for grid lines, for x-axis */
    function make_x_axis() {
	return d3.svg.axis()
	    .scale(x)
	    .orient("bottom")
	    .ticks(d3.time.days, 1)
    }

    /* Function for grid lines, for y-axis */
    function make_y_axis() {
	return d3.svg.axis()
	    .scale(y)
	    .orient("left")
	    .ticks(5)
    }
    if (typeof default_props === "undefined") {
        default_props = {};
    }

    if (!data) { return; }

    var props = {width: 250, height: 50};
    $.extend(props, default_props);
    var margin = {top: 0, right: 0, bottom: 0, left: 0},
        width = props.width - margin.left - margin.right,
        height = props.height - margin.top - margin.bottom;

    var w = Math.floor(width / data.length);

    var format_in = d3.time.format("%Y-%m-%d");
    var format_out = d3.time.format("");

    var x = d3.time.scale()
        .range([0, width]);

    var y = d3.scale.linear()
        .range([height, 0]);

    var xAxis = d3.svg.axis()
        .scale(x)
        .orient("bottom")
	.tickSize(0,0) // change to 2,2 for ticks
        .tickFormat(format_out)
        .ticks(d3.time.days, 1);

    var yAxis = d3.svg.axis()
        .scale(y)
        .orient("left")
	.tickSize(0,0) // change to 4,3 for ticks
        .ticks("") // change to 2 for y-axis tick labels
        .tickSubdivide(1);

    var area = d3.svg.area()
        .x(function(d) { return x(d.date); })
      //  .y0(height)
        .y(function(d) { return y(d.count); });

    var svg = d3.select(elem_id).append("svg")
	.attr("class", "chart-data")
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


    /* Draw the grid lines, for x-axis */
    svg.append("g")
	.attr("class", "grid")
	.attr("Transform", "translate(0, " + height + ")")
	.call(make_x_axis()
	    .tickSize(height, 0, 0)
	    .tickFormat("")
	)

    /* Draw the grid lines, for y-axis */
    svg.append("g")
	.attr("class", "grid")
	.call(make_y_axis()
	    .tickSize(-width, 0, 0)
	    .tickFormat("")
	)

    svg.append("g").attr("class", "bars").selectAll("rect")
	    .data(data)
	.enter().append("rect")
	    .attr("x", function(d) { return x(d.date); })
	    //.attr("y0", height)
	    .attr("y", function(d) { return y(d.count); })
	    .attr("width", w)
	    .attr("height", function(d) { return height - y(d.count); });

    /* draw x-axis */
    svg.append("g")
      .attr("class", "x axis")
      .attr("transform", "translate(0," + height + ")")
      .call(xAxis)
      /*.selectAll("text")
        .attr("y", -5)
        .attr("x", -30)
        .attr("transform", function(d) {
            return "rotate(-90)"
            });*/

    /* Y-axis label */
    svg.append("g")
      .attr("class", "y axis")
      .call(yAxis)
    /*.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 0)
      .attr("x", 0 - height/2)
      .attr("dy", "-3em")
      .style("text-anchor", "middle")
      .style("fill", "#777")
        .text("Messages"); */
}


function ajax_chart(elem, url, props) {
    elem = $(elem);
    $.ajax({
        dataType: "json",
        url: url,
        success: function(data) {
            chart(elem.get(0), data.evolution, props);
        },
        error: function(jqXHR, textStatus, errorThrown) {
            //alert(jqXHR.responseText);
        },
        complete: function(jqXHR, textStatus) {
            // if the list is private we have no info, remove the img anyway
            elem.find("img.ajaxloader").remove();
        }
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
    setup_attachments();
});
