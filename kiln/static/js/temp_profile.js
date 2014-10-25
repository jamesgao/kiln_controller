var tempgraph = (function(module) {
	module.Profile = function(graph, scale, schedule, start_time) {
		var end = schedule[schedule.length-1][0];
		var days = Math.floor(end / 60 / 60 / 24);
		var hours = Math.floor((end - days*60*60*24) / 60 / 60);
		var minutes = Math.ceil((end - days*60*60*24 - hours*60*60) / 60);
		var daystr = days > 0 ? days + " days, " : "";
		var hourstr = hours > 0 ? hours + " hours": "";
		var minstr = minutes > 0 ? ", "+minutes + " minutes.":".";
		this.length = end;
		this.time_total = daystr+hourstr+minstr;
		this.time_start = start_time;
		this.schedule = schedule;

		this.graph = graph;
		this.scalefunc = scale;
		this.setupGraph();
	}
	module.Profile.prototype.time_finish = function(now) {
		if (this.time_start instanceof Date) {
			return new Date(this.time_start.getTime() + this.length*1000);
		}
		return new Date(now.getTime() + this.length*1000);
	}

	module.Profile.prototype.setScale = function(scale) {
		this.scalefunc = scale;
	}
	module.Profile.prototype.setupGraph = function() {
		//immediately view range from 10 min before to end time of profile
		var now = new Date();
		var rstart = new Date(now.getTime() - 10*60*100);
		var rend = this.time_finish(now);
		this.graph.xlim(rstart, rend);

		this.pane = this.graph.pane.insert("rect", ":first-child")
			.attr("class", "profile-pane")
			.attr("height", this.graph.height)

		this.graph.zoom.on("zoom.profile", this.update.bind(this));
		this.line = this.graph.plot(this._schedule(), "profile-line", true);
		this.update();
	}
	module.Profile.prototype._schedule = function() {
		var start_time = this.time_start instanceof Date ? this.time_start : new Date();
		var schedule = [];
		for (var i = 0; i < this.schedule.length; i++) {
			var time = new Date(start_time.getTime() + this.schedule[i][0]*1000);
			var temp = this.scalefunc(this.schedule[i][1]);
			schedule.push({x:time, y:temp});
		}
		return schedule;
	}
	module.Profile.prototype.update = function() {
		var start_time = this.time_start instanceof Date ? this.time_start : new Date();
		var end_time = new Date(start_time.getTime()+this.length*1000);
		var width = this.graph.x(end_time) - this.graph.x(start_time);
		this.pane.attr("width", width)
			.attr("transform","translate("+this.graph.x(start_time)+",0)");
		
		this.graph.update("profile-line", this._schedule());
	}
	module.Profile.prototype.setScale = function(scale) {
		this.scalefunc = scale;
		this.update();
	}

	module.Profile.prototype.addNode = function() {

	}
	module.Profile.prototype.delNode = function() {

	}
	module.Profile.prototype.dragNode = function() {

	}

    return module;
}(tempgraph || {}));
