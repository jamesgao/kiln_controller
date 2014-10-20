var tempgraph = (function(module) {
	module.Monitor = function(initial) {
		this.temperature = initial;
		//default to F
		this.scalefunc = module.temp_to_F;
		this.temp_suffix = "°F"
		this.temp_prefix = ""
		
		this.graph = new tempgraph.Graph();
		this._mapped = this.temperature.map(this._map_temp.bind(this));
		this.graph.plot(this._mapped, "temperature", false);

		this.update_temp(this.last());
		this._bindUI();
	}
	module.Monitor.prototype.update_temp = function(data) {
		var now = new Date(data.time*1000.);
		var temp = this.scalefunc(data.temp);

		var minstr = now.getMinutes();
		minstr = minstr.length < 2 ? "0"+minstr : minstr;
		var nowstr = now.getHours() % 12 + ":" + minstr + (now.getHours() > 12 ? " pm" : " am");
		$("#current_time").text(nowstr);
		$("#current_temp").text(this.temp_prefix+temp+this.temp_suffix);

		//Adjust x and ylims
		if (now > this.last().time) {
			this.temperature.push(data);
			this._mapped.push({x:now, y:temp});
			
			var lims = this.graph.x.domain();
			//incoming sample needs to shift xlim
			if (now > lims[1]) {
				var start = new Date(now.getTime() - lims[1].getTime() + lims[0].getTime());
				this.graph.x.domain([start, now]);
				//If incoming sample is higher or lower than the ylims, expand that as well
				var ylims = this.graph.y.domain(), range = 2*(ylims[1] - ylims[0]);
				if (temp >= ylims[1]) {
					this.graph.y.domain([ylims[0], ylims[0]+range]);
				} else if (temp <= ylims[0]) {
					this.graph.y.domain([ylims[1]-range, ylims[1]]);
				}
			}
			this.graph.update("temperature", this._mapped);
		}

		//update the output slider and text, if necessary
		if (data.output !== undefined) {
			$("#current_output_text").text(data.output*100+"%");
			$("#current_output").val(data.output*1000);
		}
	}
	module.Monitor.prototype.update_UI = function(packet) {

	}
	module.Monitor.prototype.setProfile = function(profile) {
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

		this.update_temp(this.last());
		this.graph.update("temperature", this._mapped);
	}

	module.Monitor.prototype._map_temp = function(d) {
		return {x:new Date(d.time*1000), y:this.scalefunc(d.temp)};
	}
	module.Monitor.prototype._bindUI = function() {
		try {
			var sock = new WebSocket("ws://"+window.location.hostname+":"+window.location.port+"/ws/", "protocolOne");

			sock.onmessage = function(event) {
				var data = JSON.parse(event.data);
				this.update_temp(data);
			}.bind(this);
		} catch (e) {}
	
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

d3.json("data.json", function(error, data) {
    monitor = new tempgraph.Monitor(data);
    
});
