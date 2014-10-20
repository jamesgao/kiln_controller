var tempgraph = (function(module) {
	module.Monitor = function(initial) {
		this.temperature = initial;
		//default to F
		this.scalefunc = module.temp_to_F;
		this.temp_suffix = "°F"
		this.temp_prefix = ""
		this._mapped = this.temperature.map(this._map_temp.bind(this));
		
		this.graph = new tempgraph.Graph();
		this.graph.plot(initial.map(this._map_temp.bind(this)), "temperature", false);

		var latest = this.temperature[this.temperature.length-1];
		this.update_temp({time:latest.x/1000., temp:latest.y});
		this._bindUI();
	}
	module.Monitor.prototype.update_temp = function(data) {
		var now = new Date(data.time*1000.);
		var nowstr = now.getHours() % 12 + ":" + now.getMinutes() + (now.getHours() > 12 ? " pm" : " am");
		var temp = this.scalefunc(data.temp);
		$("#current_time").text(nowstr);
		$("#current_temp").text(this.temp_prefix+temp+this.temp_suffix);
		if (now > this.temperature[this.temperature.length-1].x) {
			this.temperature.push({x:now, y:+data.temp});
			this._mapped.push({x:now, y:temp});
			
			var lims = this.graph.xlim();
			if (now > lims[1]) {
				var start = new Date(now.getTime() - lims[1].getTime() + lims[0].getTime());
				this.graph.xlim(start, now);
			}
			this.graph.update("temperature", this._mapped);
		}

		if (data.output !== undefined) {
			$("#current_output_text").text(data.output*100+"%");
			$("#current_output").val(data.output*1000);
		}
	}
	module.Monitor.prototype.update_UI = function(packet) {

	}
	module.Monitor.prototype.setProfile = function(profile) {
	}


	module.Monitor.prototype.setScale = function(scale) {
		$("a#temp_scale_C").parent().removeClass("active");
		$("a#temp_scale_F").parent().removeClass("active");
		$("a#temp_scale_cone").parent().removeClass("active");
		if (scale == "C") {
			$("li a#temp_scale_C").parent().addClass("active");
			this.scalefunc = module.temp_to_C;
			this.graph.ylabel("Temperature (°C)")
			this.temp_suffix = "°C";
			this.temp_prefix = "";
		} else if (scale == "F") {
			$("li a#temp_scale_F").parent().addClass("active");
			this.scalefunc = module.temp_to_F;
			this.graph.ylabel("Temperature (°F)")
			this.temp_suffix = "°F";
			this.temp_prefix = "";
		} else if (scale == "cone") {
			$("li a#temp_scale_cone").parent().addClass("active");
			this.scalefunc = module.temp_to_cone;
			this.graph.ylabel("Temperature (Δ)");
			this.temp_prefix = "Δ";
			this.temp_suffix = "";
		}
		this._mapped = this.temperature.map(this._map_temp.bind(this));
		this.graph.y.domain(d3.extent(this._mapped, function(d) { return d.y; }));
		var latest = this.temperature[this.temperature.length-1];
		this.update_temp({time:latest.x/1000., temp:latest.y});
		this.graph.update("temperature", this._mapped);
	}

	module.Monitor.prototype._map_temp = function(d) {
		return {x:d.x, y:this.scalefunc(d.y)};
	}
	module.Monitor.prototype._bindUI = function() {
		/*
		var sock = new WebSocket("ws://localhost/socket/", "protocolOne");


		sock.onmessage = function(event) {
			var data = JSON.parse(event.data);
			this.update(data);
		}
		*/
		$("#temp_scale_C").click(function() { this.setScale("C");}.bind(this));
		$("#temp_scale_F").click(function() { this.setScale("F");}.bind(this));
		//$("#temp_scale_C").click(function() { this.setScale("C");}.bind(this));
	}


	module.temp_to_C = function(temp) { return temp; }
	module.temp_to_F = function(temp) {
		return temp * 9 / 5 + 32;
	}
	module.temp_to_cone = function(temp) {
		return "Not implemented"
	}

    return module;
}(tempgraph || {}));

d3.tsv("data.txt", function(error, data) {
    var newdata = [], d;
    for (var i = 0; i < data.length; i+=4) {
        d = data[i];
        newdata.push({x:new Date(d.time*1000), y:+d.temp});
    }

    monitor = new tempgraph.Monitor(newdata);
    
});
