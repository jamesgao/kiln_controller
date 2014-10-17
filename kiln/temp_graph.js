var margin = {top: 20, right: 20, bottom: 30, left: 50};
var width = $("#graph").width() - margin.left - margin.right;
var height = $("#graph").height() - margin.top - margin.bottom;

var x = d3.time.scale()
    .range([0, width]);

var y = d3.scale.linear()
    .range([height, 0]);

var xAxis = d3.svg.axis()
    .scale(x)
    .orient("bottom");

var yAxis = d3.svg.axis()
    .scale(y)
    .orient("left");

var line = d3.svg.line()
    .x(function(d) { return x(d.time); })
    .y(function(d) { return y(d.temp); });

var svg = d3.select("svg#graph")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
  .append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

var data = [{"time":1413571601.55382, "temp":14.4}, {"time":1413571606.291054, "temp":14.6}, {"time":1413571629.841126, "temp":15.8}];
data.forEach(function(d) {
  d.time = new Date(d.time*1000.);
  d.temp = +d.temp;
});

x.domain(d3.extent(data, function(d) { return d.time; }));
y.domain(d3.extent(data, function(d) { return d.temp; }));

svg.append("g")
    .attr("class", "x axis")
    .attr("transform", "translate(0," + height + ")")
    .call(xAxis);

svg.append("g")
    .attr("class", "y axis")
    .call(yAxis)
  .append("text")
    .attr("transform", "rotate(-90)")
    .attr("y", 6)
    .attr("dy", ".71em")
    .style("text-anchor", "end")
    .text("Temperature (°C)");

svg.append("path")
    .datum(data)
    .attr("class", "line")
    .attr("d", line);

svg.selectAll(".dot")
      .data(data)
    .enter().append("circle")
      .attr("class", "dot")
      .attr("r", 3.5)
      .attr("cx", function(d) { return x(d.time); })
      .attr("cy", function(d) { return y(d.temp); });

function draw() {
  svg.select("g.x.axis").call(xAxis);
  svg.select("g.y.axis").call(yAxis);
  svg.select("path.line").attr("d", line);
  svg.selectAll(".dot").data(data)
    .attr("cx", function(d) {return x(d.time);})
    .attr("cy", function(d) {return y(d.temp);});
}

function update() {
  x.domain([new Date(data[0].time.getTime() - 5000), new Date(data[2].time.getTime() + 5000)]);
  draw();
}