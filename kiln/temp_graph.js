var tempgraph = (function(module) {
    module.graph_defaults = {
        margin: {top: 20, right: 20, bottom: 30, left: 50},
        object: "#graph",
        show_axes: true,
    }
    module.Graph = function(options) {
        //Options: margin, width, height, object
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
        this.svg.append("defs").append("rect")
            .attr("class", "pane")
            .attr("width", this.width)
            .attr("height", this.height);
        this.axes = this.svg.append("g")
            .attr("class", "axes")
            .attr("transform", "translate("+this.margin.left+","+this.margin.top+")")
            .attr("clip-path", "url(#pane)");

        this.x = d3.time.scale().range([0, this.width]);
        this.y = d3.scale.linear().range([this.height, 0]);

        this.zoom = d3.behavior.zoom().on("zoom", this.draw.bind(this));

        if (options.show_axes === undefined || options.show_axes) {
            this.x_axis = d3.svg.axis().scale(this.x).orient("bottom");
            this.y_axis = d3.svg.axis().scale(this.y).orient("left");

            //setup axies labels and ticks
            this.axes.append("g")
                .attr("class", "x axis")
                .attr("transform", "translate(0," + this.height + ")")
                .call(this.x_axis);

            this.axes.append("g")
                    .attr("class", "y axis")
                    .call(this.y_axis)
                .append("text")
                    .attr("transform", "rotate(-90)")
                    .attr("y", 6)
                    .attr("dy", ".71em")
                    .style("text-anchor", "end")
                    .text("Temperature (°F)");

        }
        window.onresize = this.resize.bind(this);
        this.lines = [];
    };
    module.Graph.prototype.plot = function(data, marker) {
        var line = d3.svg.line()
            .x(function(d) { return this.x(d.x); }.bind(this))
            .y(function(d) { return this.y(d.y); }.bind(this));
        this.axes.append("path")
            .datum(data)
            .attr("class", "line")
            .attr("d", line);

        if (marker !== undefined && marker) {
            var marker = this.axes.append("g")
                .selectAll(".dot").data(data)
                .enter().append("circle")
                    .attr("class", "dot")
                    .attr("r", 5)
                    .attr("cx", function(d) { return this.x(d.x); }.bind(this))
                    .attr("cy", function(d) { return this.y(d.y); }.bind(this));
        }
        this.lines.push({line:line, data:data, marker:marker});

        this.x.domain(d3.extent(data, function(d) { return d.x; }));
        this.y.domain(d3.extent(data, function(d) { return d.y; }));
        this.zoom.x(this.x);
        this.svg.call(this.zoom);
        this.draw();
        return line;
    }
    module.Graph.prototype.draw = function() {
        this.svg.select("g.x.axis").call(this.x_axis);
        this.svg.select("g.y.axis").call(this.y_axis);
        var line, data, marker;
        for (var i = 0; i < this.lines.length; i++) {
            line = this.lines[i].line;
            data = this.lines[i].data;
            marker = this.lines[i].marker;
            if (marker !== undefined) {
                this.svg.selectAll(".dot").data(data)
                    .attr("cx", function(d) { return this.x(d.x)}.bind(this))
                    .attr("cy", function(d) { return this.y(d.y)}.bind(this));
            }
            this.svg.select("path.line").attr("d", line);
        }
        console.log("draw");
    }
    module.Graph.prototype.resize = function() {
        var margin = this.margin;
        var width = $(this.obj).width() - margin.left - margin.right;
        var height = $(this.obj).height() - margin.top - margin.bottom;

        this.svg
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
        this.svg.select("rect.pane")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
        this.x.range([0, width]);
        this.y.range([height, 0]);

        this.width = width;
        this.height = height;
        this.draw();
        console.log("resized");
    }

    module.Graph.prototype.update = function(line, data) {
        for (var i = 0; i < this.lines.length; i++) {
            if (this.lines[i].line === line) {
                this.axes.select("path.line").datum(data).attr("d", line);
            }
        }
        this.draw();
    }
    module.Graph.prototype.xlim = function(min, max) {
        this.x.domain([min, max]);
    }

    return module;
}(tempgraph || {}));

var data = d3.tsv("data.txt", function(error, data) {
    data.forEach(function(d) {
        d.x = new Date(d.time*1000.);
        d.y = +d.temp*9/5+32;
    });

    graph = new tempgraph.Graph()
    line = graph.plot(data, false);
});


function update() {
    d3.tsv("data2.txt", function(error, data) {
        data.forEach(function(d) {
            d.x = new Date(d.time*1000.);
            d.y = +d.temp;
        });

        var lim = d3.extent(data, function(d){return d.x;});
        graph.xlim(lim[0], lim[1]);
        graph.update(line, data);
        console.log("done!");
    })
}
