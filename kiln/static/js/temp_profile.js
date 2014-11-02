var tempgraph = (function(module) {
	module.Profile = function(graph, scale, schedule, start_time, running) {
		var end = schedule[schedule.length-1][0];
		this.length = end;
		this.time_total = juration.stringify(end);
		this.time_start = start_time;
		this.schedule = schedule;
		this.running = running === undefined ? false : running;

		this.graph = graph;
		this.scalefunc = scale;

		this.drag_start = d3.behavior.drag()
			.on("dragstart", function() {
				d3.event.sourceEvent.stopPropagation();
			}).on("drag.profile", this.dragStart.bind(this));

		//Generate the highlight pane to indicate where the profile is running
		this.pane_stroke = this.graph.pane.insert("line", ":first-child")
			.attr("class", "profile-pane-stroke")
			.attr("y1", 0).attr("y2", this.graph.height)
			.call(this.drag_start);
		this.pane = this.graph.pane.insert("rect", ":first-child")
			.attr("class", "profile-pane")
			.attr("height", this.graph.height)
			.attr("clip-path", "url(#pane)");

		this.line = this.graph.plot(this._schedule(), "profile-line", true);

		//immediately view range from 10 min before to end time of profile
		var now = new Date();
		var rstart = new Date(now.getTime() - 10*60*100);
		var rend = this.time_finish(now);
		this.graph.xlim(rstart, rend);

		this.drag = d3.behavior.drag().origin(function(d) { 
			return {x:this.graph.x(d.x), y:this.graph.y(d.y)};
		}.bind(this)).on("dragstart", function(d) {
			d3.event.sourceEvent.stopPropagation();
			this._node = this._findNode(d);
		}.bind(this));

		this.update();

		//events
		this._bindUI();
	}
	module.Profile.prototype.time_finish = function() {
		var now = this.time_start instanceof Date ? this.time_start : new Date();
		return new Date(now.getTime() + this.length*1000);
	}

	module.Profile.prototype.setScale = function(scale) {
		this.scalefunc = scale;
		this.update();
	}
	module.Profile.prototype.update = function() {
		var start_time = this.time_start instanceof Date ? this.time_start : new Date();
		var end_time = new Date(start_time.getTime()+this.length*1000);
		var width = this.graph.x(end_time) - this.graph.x(start_time);
		var x = this.graph.x(start_time);
		this.pane.attr("width", width)
			.attr("transform","translate("+this.graph.x(start_time)+",0)");
		this.pane_stroke.attr("x1", x).attr("x2", x);

		var join = this.graph.update("profile-line", this._schedule());
		join.on("mouseover.profile", this.hoverNode.bind(this))
			.on("mouseout.profile", this._hideInfo.bind(this))
			.on("dblclick.profile", this.delNode.bind(this));
		join.call(this.drag);

		//update the profile info box
		var start = this.time_start instanceof Date ? module.format_time(this.time_start) : "Not started";
		var finish = this.time_finish();
		var remain = (finish - (new Date())) / 1000;
		$("#profile_time_finish").text(module.format_time(finish));
		$("#profile_time_start").text(start);
		$("#profile_time_remain").text(juration.stringify(remain));
	}
	
	module.Profile.prototype._bindUI = function() {
		$("#profile_name").attr("disabled", "disabled");
		$("#profile_actions .btn-success").click(this.save.bind(this));
		$("#profile_actions .btn-primary").click(this.start.bind(this));
		$("#profile_actions .btn-default").click(this.pause.bind(this));
		
		// Info pane events
		var updateNode = function() {
			clearTimeout(this.timeout_infoedit);
			var time = juration.parse($("#profile-node-info input.time").val());
			var temp = parseFloat($("#profile-node-info input.temp").val());
			this._updateNode(this._node, time, temp);
		}.bind(this)

		$("#profile-node-info").on("mouseout.profile", this._hideInfo.bind(this));
		$("#profile-node-info").on("mouseover.profile", function() {
			clearTimeout(this.timeout_infohide);
		}.bind(this));
		$("#profile-node-info input").on("keypress", function(e) {
			clearTimeout(this.timeout_infoedit);
			if (e.keyCode == 13) {
				updateNode();
			} else {
				this.timeout_infoedit = setTimeout(updateNode, 2000);
			}
		}.bind(this));
		$("#profile-node-info input").on("blur", function() {
			this._focused = false;
			updateNode();
			this._hideInfo();
		}.bind(this));
		$("#profile-node-info input").on("focus", function() {
			this._focused = true;
		}.bind(this));

		//Graph events
		this.graph.zoom.on("zoom.profile", this.update.bind(this));
		this.setState();
	}
	module.Profile.prototype._schedule = function() {
		var start_time = this.time_start instanceof Date ? this.time_start : new Date();
		var schedule = [];
		for (var i = 0; i < this.schedule.length; i++) {
			var time = new Date(start_time.getTime() + this.schedule[i][0]*1000);
			var temp = this.scalefunc.scale(this.schedule[i][1]);
			schedule.push({id:i, x:time, y:temp});
		}
		return schedule;
	}
	module.Profile.prototype._hideInfo = function() {
		this.timeout_infohide = setTimeout(function() {	
			if (!this._focused)
				$("#profile-node-info").fadeOut(100); 
		}.bind(this), 250);
	}
	module.Profile.prototype._findNode = function(d) {
		return d.id;
	}
	module.Profile.prototype._updateNode = function(node, time, temp) {
		var start_time = this.time_start instanceof Date ? this.time_start : new Date();
		if (!(time instanceof Date)) {
			//This is probably just a direct offset, no need to compute time
			this.schedule[node][0] = time;
		} else if (node == 0) {
			this.schedule[node][0] = 0;
		} else {
			var newtime = (time - start_time.getTime()) / 1000;
			this.schedule[node][0] = newtime;
		}
		//update length only if we're editing the final node
		if (node == this.schedule.length-1) {
			this.length = this.schedule[node][0];
		}
		this.schedule[node][1] = this.scalefunc.inverse(temp);

		//if we're dragging this node "behind" the previous, push it back as well
		//except if the previous one is the first node, in which case just set it to zero
		if (node > 0 && this.schedule[node-1][0] >= newtime) {
			if (node-1 == 0)
				this.schedule[node][0] = 0;
			else
				this.schedule[node-1][0] = newtime;
		} else if (node < this.schedule.length-1 && this.schedule[node+1][0] < newtime){
			this.schedule[node+1][0] = newtime;
			if (node+1 == this.schedule.length-1)
				this.length = this.schedule[node+1][0];
		}
		this._showInfo(node);
		this.update();

		//Unlock the save buttons and names
		$("#profile_name").removeAttr("disabled");
		$("#profile_actions .btn-success").removeClass("disabled");
		$("#profile_actions .btn-primary").addClass("disabled");
	}
	module.Profile.prototype._showInfo = function(node) {
		this._node = node;
		var start_time = this.time_start instanceof Date ? this.time_start : new Date();
		var time = new Date(this.schedule[node][0]*1000 + start_time.getTime());
		var temp = this.scalefunc.scale(this.schedule[node][1]);
		$("#profile-node-info")
			.css('left', this.graph.x(time)+80)
			.css('top', this.graph.y(temp)+50)
			.fadeIn(100);

		$("#profile-node-info div.name").text("Set point "+(node+1));
		$("#profile-node-info input.temp").val(this.scalefunc.print(Math.round(temp*100)/100));
		var timestr;
		try {
			timestr = juration.stringify(this.schedule[node][0]);
		} catch (e) { 
			timestr = 0;
		}
		$("#profile-node-info input.time").val(timestr);
	}
	module.Profile.prototype.addNode = function() {
		d3.event.stopPropagation();
		var mouse = d3.mouse(this.graph.pane[0][0]);
		var start_time = this.time_start instanceof Date ? this.time_start : new Date();

		var secs = (this.graph.x.invert(mouse[0]) - start_time) / 1000;

		var start, end;
		for (var i = 0; i < this.schedule.length-1; i++) {
			start = this.schedule[i][0];
			end = this.schedule[i+1][0];
			if (start < secs && secs < end) {
				var t2 = this.schedule[i+1][1], t1 = this.schedule[i][1];
				var frac = (secs - start) / (end - start);
				var temp = frac * (t2 - t1) + t1;
				this.schedule.splice(i+1, 0, [secs, temp]);
			}
		}
		this.update();
		$("#profile_name").removeAttr("disabled");
		$("#profile_actions .btn-success").removeClass("disabled");
		$("#profile_actions .btn-primary").addClass("disabled");
	}
	module.Profile.prototype.delNode = function(d) {
		d3.event.stopPropagation();
		var node = this._findNode(d);
		//ignore attempts to delete the starting and ending nodes
		if (node != 0 && this.schedule.length > 2) {
			this.schedule.splice(node, 1);
			if (node == this.schedule.length) {
				this.length = this.schedule[node-1][0];
			}
		}
		this.update();
		$("#profile_name").removeAttr("disabled");
		$("#profile_actions .btn-success").removeClass("disabled");
		$("#profile_actions .btn-primary").addClass("disabled");
	}
	module.Profile.prototype.dragNode = function(d) {
		var time = this.graph.x.invert(d3.event.x);
		var temp = this.graph.y.invert(d3.event.y);
		this._updateNode(d.id, time, temp);
	}
	module.Profile.prototype.hoverNode = function(d) {
		clearTimeout(this.timeout_infohide);
		this._showInfo(d.id);
	}
	module.Profile.prototype.dragStart = function() {
		this.time_start = this.graph.x.invert(d3.event.x);
		if (this.time_start > new Date())
			this.time_start = null;
		this.update();
	}

	module.Profile.prototype.save = function() {
		//convert name into filename
		var rawname = $("#profile_name").val();
		var name = rawname.replace(/ /gi, "_");
		name = name.replace(/Δ/gi, "^");
		name += ".json";

		var post = {schedule:JSON.stringify(this.schedule)};

		$.post("/profile/"+name, post).done(function(result) {
			if (result.type == "success") {
				$("#profile_name").attr("disabled", "disabled");
				$("#profile_actions .btn-success").addClass("disabled");
				//Check if the name exists in the menu, otherwise add new entry
				var notnew = false;
				$("#profile_list a").each(function() {	
					console.log($(this).data("fname"), $(this).data("fname") == name);
					notnew = $(this).data("fname") == name || notnew; 
				});
				if (!notnew) {
					//Add a new entry into the profile list dropdown
					$("#profile_list li").removeClass("active");
					var html = "<li><a href='#' data-fname='"+name+"' class='active'>"+rawname+"</a></li>";
					$("#profile_list").append(html).addClass("active").select("a")
						.click(function(e) {
							$("#profile_list a").removeClass("active");
							$(e.target).addClass("active");
							$("#profile_name").val($(e.target).text());
							var fname = $(e.target).attr("data-fname");
							this.cleanup();
							$.getJSON("/profile/"+fname, function(data) {
								monitor.setProfile(data);
							});
						}.bind(this));
				}
				this.setState(false);
			} else if (result.type == "error") {
				alert(result.msg);
			}
		}.bind(this));

	}
	module.Profile.prototype.setState = function(running) {
		this.running = running === undefined ? this.running : running;
		console.log("Set State: ", this.running);
		if (this.running) {
			this.line.marker.on("dblclick.profile", null);
			this.graph.pane.on("dblclick.profile", null);
			$("#profile-node-info input").attr("disabled", "disabled");
			this.drag.on("drag.profile", null);
			this.drag_start.on("drag.profile", null);
			$("#profile_actions .btn-success").addClass("disabled");
			$("#profile_actions .btn-primary").addClass("disabled");
			$("#profile_actions .btn-default").removeClass("disabled");
		} else {
			this.line.marker.on("dblclick.profile", this.delNode.bind(this));
			this.graph.pane.on("dblclick.profile", this.addNode.bind(this));
			$("#profile-node-info input").removeAttr("disabled");
			this.drag.on("drag.profile", this.dragNode.bind(this));
			this.drag_start.on("drag.profile", this.dragStart.bind(this));
			$("#profile_actions .btn-success").addClass("disabled");
			$("#profile_actions .btn-primary").removeClass("disabled");
			$("#profile_actions .btn-default").addClass("disabled");
		}
	}
	module.Profile.prototype.cleanup = function() {
		this.graph.remove("profile-line");
		this.pane.remove();
		this.pane_stroke.remove();
	}
	module.Profile.prototype.pause = function() {
		$("#profile_actions .btn-default").addClass("disabled");

		//TODO: ajax query
		this.setState(false)
	}
	module.Profile.prototype.start = function() {
		$("#profile_actions .btn-primary").addClass("disabled");

		//TODO: ajax query
		//This should be done by the query
		this.setState(true);
		if (!(this.time_start instanceof Date))
			this.time_start = new Date();
	}


    return module;
}(tempgraph || {}));
