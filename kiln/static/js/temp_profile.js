var tempgraph = (function(module) {
	module.Profile = function(schedule, start_time) {
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
	}
	module.Profile.prototype.time_finish = function(now) {
		if (this.time_start instanceof Date) {
			return new Date(this.time_start.getTime() + this.length*1000);
		}
		return new Date(now.getTime() + this.length*1000);
	}

    return module;
}(tempgraph || {}));
