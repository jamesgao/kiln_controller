var tempgraph = (function(module) {
	module.Monitor = function(initial) {
		this.temperature = initial;
		this.profile = null;
		//default to F
		this.scalefunc = new module.TempScale("F");
		
		this.graph = new module.Graph();
		this._mapped = this.temperature.map(this._map_temp.bind(this));
		this.graph.plot(this._mapped, "temperature", false);

		this.updateTemp(this.last());
		this._bindUI();
	}
	module.Monitor.prototype.updateTemp = function(data) {
		var now = new Date(data.time*1000.);
		var temp = this.scalefunc.scale(data.temp);

		var nowstr = module.format_time(now);
		$("#current_time").text(nowstr);
		$("#current_temp").text(this.scalefunc.print(Math.round(temp*100) / 100));

		//Adjust x and ylims
		if (now > this.last().time) {
			this.temperature.push(data);
			this._mapped.push({x:now, y:temp});
			
			var lims = this.graph.x.domain();
			//incoming sample needs to shift xlim
			if (now > lims[1]) {
				var start = new Date(now.getTime() - lims[1].getTime() + lims[0].getTime());
				this.graph.x.domain([start, now]);
			}

			//If incoming sample is higher or lower than the ylims, expand that as well
			var ylims = this.graph.y.domain();
			if (temp >= ylims[1] || temp <= ylims[0]) {
				this.graph.recenter(.2);
			}
			this.graph.update("temperature", this._mapped);
		}

		//update the output slider and text, if necessary
		if (data.output !== undefined) {
			if (data.output == -1) {
				$("#current_output_text").text("Off");
				$("#current_output").val(0);
			} else {
				var outstr = Math.round(data.output*10000) / 100;
				$("#current_output_text").text(outstr+"%");
				$("#current_output").val(data.output*1000);
			}
		}

		//update the profile
		if (this.profile)
			this.profile.update();
	}
	module.Monitor.prototype.setProfile = function(schedule, start_time) {
		this.profile = new module.Profile(this.graph, this.scalefunc, schedule, start_time);
		var start = this.profile.time_start === undefined ? 
			"Not started" : module.format_time(start_time);
		$("#profile_time_total").text(this.profile.time_total);
		$("#profile_time_start").text(start);
		//$("#profile_time_finish") = this.profile.time_finish();
		$("#profile_info, #profile_actions").hide().removeClass("hidden").slideDown();
		return this.profile;
	}
	module.Monitor.prototype.last = function() {
		return this.temperature[this.temperature.length-1];
	}
	
	module.Monitor.prototype.setScale = function(scale) {
		$("a#temp_scale_C").parent().removeClass("active");
		$("a#temp_scale_F").parent().removeClass("active");
		$("a#temp_scale_cone").parent().removeClass("active");
		if (scale == "C") {
			$("li a#temp_scale_C").parent().addClass("active");
			this.scalefunc = new module.TempScale("C");
			this.graph.ylabel("Temperature (°C)")
		} else if (scale == "F") {
			$("li a#temp_scale_F").parent().addClass("active");
			this.scalefunc = new module.TempScale("F");
			this.graph.ylabel("Temperature (°F)")
		} else if (scale == "cone") {
			$("li a#temp_scale_cone").parent().addClass("active");
			this.scalefunc = new module.TempScale("cone");
			this.graph.ylabel("Temperature (Δ)");
		}
		this._mapped = this.temperature.map(this._map_temp.bind(this));
		this.graph.y.domain(d3.extent(this._mapped, function(d) { return d.y; }));

		this.updateTemp(this.last());
		this.graph.update("temperature", this._mapped);
		if (this.profile)
			this.profile.setScale(this.scalefunc);
	}

	module.Monitor.prototype._map_temp = function(d) {
		return {x:new Date(d.time*1000), y:this.scalefunc.scale(d.temp)};
	}

	module.Monitor.prototype.setState = function(name, data) {
		if (name == "Lit" || name =="Running") {
			$("#ignite_button").addClass("disabled");
			$("#current_output").removeAttr("disabled");
			$("#stop_button").removeClass("disabled");
			$("#stop_button_navbar").removeClass("hidden disabled");
			$("#profile_select").removeClass("disabled");
		} else if (name == "Idle" || name == "Cooling") {
			$("#ignite_button").removeClass("disabled");
			$("#current_output").attr("disabled", "disabled");
			$("#stop_button").addClass("disabled");
			$("#stop_button_navbar").addClass("hidden disabled");
			$("#profile_select").removeClass("disabled");
		} 
		if (name == "Running") {
			if (data !== undefined) {
				this.setProfile(data.schedule, new Date(data.start_time*1000));
			}
			this.profile.setState(true);
		} else if (this.profile === undefined) {
			this.profile.setState(false);
		}
	}
	module.Monitor.prototype._bindUI = function() {
		$("#temp_scale_C").click(function() { this.setScale("C");}.bind(this));
		$("#temp_scale_F").click(function() { this.setScale("F");}.bind(this));
		//$("#temp_scale_C").click(function() { this.setScale("C");}.bind(this));

		$("#profile_name").val("");

		$("#ignite_button").click(function() {
			this._disable_all();
			$.getJSON("/do/ignite", function(data) {
				if (data.type == "error")
					alert(data.msg, data.error);
			});
		}.bind(this));

		$("#stop_button, #stop_button_navbar").click(function() {
			this._disable_all();
			$.getJSON("/do/shutoff", function(data) {
				if (data.type == "error")
					alert(data.msg, data.error);
				else if (data.type == "success") {
					$("#current_output").val(0);
				}
			});
		}.bind(this));

		$("#current_output").mouseup(function(e) {
			$.getJSON("/do/set?value="+(e.target.value / 1000), function(data) {
				if (data.type == "error")
					alert(data.msg, data.error);
				else if (data.type == "success")
					$("#current_output_text").text(e.target.value/10 + "%");
			})
		});

		$("#profile_list a").click(function(e) {
			$("#profile_list li").removeClass("active");
			$(e.target).parent().addClass("active");
			$("#profile_name").val($(e.target).text());
			var fname = $(e.target).attr("data-fname");
			if (this.profile)
				this.profile.cleanup();
			$.getJSON("/profile/"+fname, function(data) {
				this.setProfile(data);
			}.bind(this));
		}.bind(this));

		try {
			var sock = new WebSocket("ws://"+window.location.hostname+":"+window.location.port+"/ws/");

			sock.onmessage = function(event) {
				var data = JSON.parse(event.data);
				if (data.type == "temperature")
					this.updateTemp(data);
				else if (data.type == "state") {
					this.setState(data.state);
				}
			}.bind(this);
		} catch (e) {}
	}

	module.Monitor.prototype._disable_all = function() {
		$("button").addClass("disabled");
		$("input").attr("disabled", "disabled");
	}


	module.TempScale = function(name) {
		if (name == "C") {
			this.scale = function(t) { return t;};
			this.inverse = function(t) { return t;};
			this.print = function(t) { return t+"°C"}
		} else if (name == "F") {
			this.scale = function(temp) { return temp * 9 / 5 + 32; }
			this.inverse = function(temp) {	return (temp - 32) * 5 / 9;}
			this.print = function(t) { return t+"°F"}
		} else if (name == "cone") {
			
		}
	}
	module.TempScale.C_to_cone = function(temp) {
		var cones = [600,614,635,683,717,747,792,804,838,852,884,894,900,923,955,984,999,1046,1060,1101,1120,1137,1154,1162,1168,1186,1196,1222,1240,1263,1280,1305,1315,1326,1346]
		var names = [];
		for (var i = -22; i < 0; i++) {
			names.push("0"+(""+i).slice(1));
		}
		for (var i = 1; i < 14; i++) {
			names.push(""+i);
		}
		return cones, names
	}

	module.format_time = function(now) {
		if (!(now instanceof Date))
			now = new Date(now);
		var hourstr = now.getHours() % 12;
		hourstr = hourstr == 0 ? 12 : hourstr;
		var minstr = now.getMinutes();
		minstr = minstr < 10 ? "0"+minstr : minstr;
		return hourstr + ":" + minstr + (now.getHours() >= 12 ? " pm" : " am");
	}

    return module;
}(tempgraph || {}));
