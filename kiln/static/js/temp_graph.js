var tempgraph = (function(module) {
    module.graph_defaults = {
        margin: {top: 20, right: 20, bottom: 30, left: 50},
        object: "#graph",
        show_axes: true,
    }
    module.Graph = function(options) {
        if (options === undefined)
            options = module.graph_defaults;

        if (options.object !== undefined)
            this.obj = options.object;
        else
            this.obj = document.createElementNS("http://www.w3.org/2000/svg", "svg");

        this.margin = options.margin;
        this.width = options.width ? options.width : $(this.obj).width() - this.margin.left - this.margin.right;
        this.height = options.height ? options.height : $(this.obj).height() - this.margin.top - options.margin.bottom;

        this.svg = d3.select(this.obj);
        this.svg.append("defs").append("clipPath").attr("id", "pane")
            .append("rect")
                .attr("width", this.width)
                .attr("height", this.height);

        this.pane = this.svg.append("g")
            .attr("transform", "translate("+this.margin.left+","+this.margin.top+")")

        /*xfm.append("rect")
            .attr("style", "fill:#DDD")
            .attr("width", this.width)
            .attr("height", this.height);*/

        this.x = d3.time.scale().range([0, this.width]);
        this.y = d3.scale.linear().range([this.height, 0]);

        this.zoom = d3.behavior.zoom(this.obj).on("zoom", this.draw.bind(this))
            .on("zoomend", this.recenter.bind(this, .2));

        if (options.show_axes === undefined || options.show_axes) {
            this.x_axis = d3.svg.axis().scale(this.x).orient("bottom")
                .tickSize(this.height).tickSubdivide(true);
            this.y_axis = d3.svg.axis().scale(this.y).orient("left")
                .tickSize(this.width).tickSubdivide(true);

            //setup axies labels and ticks
            this.pane.append("g")
                .attr("class", "x axis")
                //.attr("transform", "translate(0," + this.height + ")")
                .call(this.x_axis);

            this.pane.append("g")
                    .attr("class", "y axis")
                    .attr("transform", "translate("+this.width+", 0)")
                    .call(this.y_axis)
                .append("text")
                    .attr("class", "ylabel")
                    .attr("transform", "translate(-"+this.width+",0)rotate(-90)")
                    .attr("y", 6)
                    .attr("dy", ".71em")
                    .style("text-anchor", "end")
                    .text("Temperature (°F)");

        }

        this.axes = this.pane.append("g")
            .attr("class", "axes")
            .attr("style", "clip-path:url(#pane)");
        window.onresize = this.resize.bind(this);
        this.lines = {};
    };
    module.Graph.prototype.plot = function(data, className, marker) {
        this.x.domain(d3.extent(data, function(d) { return d.x; }));
        this.zoom.x(this.x);

        var line = d3.svg.line()
            .x(function(d) { return this.x(d.x); }.bind(this))
            .y(function(d) { return this.y(d.y); }.bind(this));
        
        this.axes.append("path")
            .datum(data)
            .attr("class", className)
            .attr("d", line);

        if (marker !== undefined && marker) {
            var selector = className.replace(/ /gi, ".");
            var key = data.id === undefined ? undefined : function(d){ return d.id;};
            var marker = this.axes.append("g").selectAll("."+selector+".dot")
                .data(data, key).enter().append("circle")
                    .attr("class", className+" dot")
                    .attr("r", 10)
                    .attr("cx", function(d) { return this.x(d.x); }.bind(this))
                    .attr("cy", function(d) { return this.y(d.y); }.bind(this));
        }

        this.lines[className] = {line:line, data:data, marker:marker};
        this.svg.call(this.zoom);
        this.draw();
        this.recenter(.2);
        return this.lines[className];
    }
    module.Graph.prototype.draw = function() {
        this.svg.select("g.x.axis").call(this.x_axis);
        this.svg.select("g.y.axis").call(this.y_axis);
        var line, data, marker;
        for (var name in this.lines) {
            line = this.lines[name].line;
            data = this.lines[name].data;
            marker = this.lines[name].marker;
            if (marker !== undefined) {
                this.axes.selectAll(".dot").data(data)
                    .attr("cx", function(d) { return this.x(d.x)}.bind(this))
                    .attr("cy", function(d) { return this.y(d.y)}.bind(this));
            }
            this.svg.select("path."+name).attr("d", line);
        }
    }
    module.Graph.prototype.resize = function() {
        var margin = this.margin;
        var width = $(this.obj).width() - margin.left - margin.right;
        var height = $(this.obj).height() - margin.top - margin.bottom;

        this.svg
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
        this.x.range([0, width]);
        this.y.range([height, 0]);

        this.width = width;
        this.height = height;
        this.draw();
    }
    module.Graph.prototype.recenter = function(margin) {
        //Argument margin gives the fraction of (max - min) to add to the margin
        //Defaults to 0
        var extent = [], data, valid,
            low = this.x.domain()[0], high=this.x.domain()[1];

        for (var name in this.lines) {
            data = this.lines[name].data;
            valid = data.filter(function(d) { return low <= d.x && d.x <= high; })
            extent = extent.concat(valid);
        }
        extent = d3.extent(extent, function(d){return d.y});
        if (margin > 0) {
            var range = extent[1]-extent[0];
            extent[0] -= margin*range;
            extent[1] += margin*range;
        }
        this.y.domain(extent);
        this.draw();
    }
    module.Graph.prototype.update = function(className, data) {
        this.lines[className].data = data;
        this.axes.select("path."+className).datum(data)
            .attr("d", this.lines[className].line);

        var join, selector;
        if (this.lines[className].marker) {
            selector = className.replace(/ /gi, ".");
            join = this.axes.selectAll("."+selector+".dot")
                .data(data, function(d){ return d.id;});
            join.enter().append("circle")
                .attr("class", className+" dot")
                .attr("r", 10);
            join.exit().remove();
            join.attr("cx", function(d) { return this.x(d.x); }.bind(this))
                .attr("cy", function(d) { return this.y(d.y); }.bind(this));
        }
        this.draw();
        return join;
    }
    module.Graph.prototype.xlim = function(min, max) {
        if (min === undefined)
            return this.x.domain();

        this.x.domain([min, max]);
        this.draw();
    }
    module.Graph.prototype.ylim = function(min, max) {
        if (min === undefined)
            return this.y.domain();

        this.y.domain([min, max]);
        this.draw();
    }
    module.Graph.prototype.ylabel = function(text) {
        this.svg.select(".ylabel").text(text);
    }

    module.Graph.prototype.remove = function(className) {
        var selector = className.replace(/ /gi, ".");
        this.axes.selectAll("path."+selector).remove();
        if (this.lines[className].marker) {
            this.axes.selectAll("."+selector+".dot").remove();
        }
        delete this.lines[className];
    }

    return module;
}(tempgraph || {}));

