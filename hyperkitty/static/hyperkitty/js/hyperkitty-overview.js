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
 * Recent activity graph (area graph)
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
    
    var data = merge(dates, counts);
    var margin = {top: 20, right: 20, bottom: 50, left: 40},
        width = 350 - margin.left - margin.right,
        height = 150 - margin.top - margin.bottom;

    var format_in = d3.time.format("%Y-%m-%d");
    var format_out = d3.time.format("");

    var x = d3.time.scale()
        .range([0, width]);

    var y = d3.scale.linear()
        .range([height, 0]);

    var xAxis = d3.svg.axis()
        .scale(x)
        .orient("bottom")
	.tickSize(2,2)
        .tickFormat(format_out)
        .ticks(d3.time.days, 1);
	
    var yAxis = d3.svg.axis()
        .scale(y)
        .orient("left")
	.tickSize(4,3)
        .ticks(2)
        .tickSubdivide(1);

    var area = d3.svg.area()
	.interpolate("monotone")
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

    /* Y-axis label */
    svg.append("g")
      .attr("class", "y axis")
      .call(yAxis)
    .append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 0)
      .attr("x", 0 - height/2)
      .attr("dy", "-3em")
      .style("text-anchor", "middle")
      .style("fill", "#777")
      .text("Messages");
    
}


/*
 * Recent activity bar chart
 */
function chart(elem_id, dates, counts, baseurl) {
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
    
    var data = merge(dates, counts);
    var margin = {top: 0, right: 0, bottom: 0, left: 0},
        width = 200 - margin.left - margin.right,
        height = 50 - margin.top - margin.bottom;
	
    var w = 5;

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
	.attr("id", "chart-data")
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

    svg.append("g").attr("class","bars").selectAll("rect")
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
