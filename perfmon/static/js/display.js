//====================================================================================
//                                H E L P E R S
//====================================================================================

var formatData = function(data) {
	var suffixes = ["b", "kb", "mb", "gb", "tb", "pb", "eb", "zb", "yb"];
	var x = data;
	var i = 0;
	
	while (x >= 1024) {
		i++;
		x /= 1024;
	}
	
	return (Math.ceil(x * 100) / 100) + " " + suffixes[i];
}




//====================================================================================
//                       H E A T M A P  P L O T S (CalHeatMap)
//====================================================================================

var now = new Date();
var start = now.setDate(now.getDate()-13);

var cal_response = new CalHeatMap();
cal_response.init({
    data: "query/ds/response",
    id: "response",
    browsing: true,
    domain : "day",
    subDomain : "hour",
    start: start,
    range : 15,
    cellsize: 10,
    cellpadding: 1,
    domainGutter: 2,
    scale: [1, 10, 100, 1000],    // Custom threshold for the scale
    itemName : ["second", "seconds"],
});

var cal_downstream = new CalHeatMap();
cal_downstream.init({
    data: "query/ds/throughput/downstream",
    id: "downstream",
    browsing: true,
    domain : "day",
    subDomain : "hour",
    start: start,
    range : 15,
    cellsize: 10,
    cellpadding: 1,
    domainGutter: 2,
    scale: [1e3, 1e4, 1e5, 1e6],    // Custom threshold for the scale
    itemName : ["byte", "bytes"],
});

var cal_downstream = new CalHeatMap();
cal_downstream.init({
    data: "query/ds/throughput/upstream",
    id: "upstream",
    browsing: true,
    domain : "day",
    subDomain : "hour",
    start: start,
    range : 15,
    cellsize: 10,
    cellpadding: 1,
    domainGutter: 2,
    scale: [1e3, 1e4, 1e5, 1e6],    // Custom threshold for the scale
    itemName : ["byte", "bytes"],
});




//====================================================================================
//                       R E A L - T I M E  P L O T S (cubism)
//====================================================================================

// Cubism.js config
var context = cubism.context()
    .serverDelay(100)
    .clientDelay(100)
    .step(1e3*60)
    .size(700);

// Cubism.js timeseries metric contsructor for an endpoint and type
var create_metric = function(endpoint, type) {
  return context.metric(function(start, stop, step, callback) {
    d3.json("/query/ts/"+type+"/"+encodeURIComponent(endpoint)+"/"+start.getTime()+"/"+stop.getTime()+"/"+step, function(data) {
      if (!data) return callback(new Error("unable to load data"));
      callback(null, data);
    });
  }, endpoint);
}

//
// Real-time response graphs
//
d3.select("#rt-response").call(function(div) {

  div.append("div")
      .attr("class", "axis")
      .call(context.axis().orient("top"));
  
  d3.json("query/endpoints/", function(endpoints) {
	  var metrics = [];
	  $.each(endpoints, function(i, endpoint) {
	  	metrics.push(create_metric(endpoint, 'response'));
	  });
	  div.selectAll(".horizon")
	    .data(metrics)
	    .enter().append("div")
	    .attr("class", "horizon")
	    .call(context.horizon()
	  	        .height(30)
	  	        .extent([0, 5]));
  });
  
  div.append("div")
      .attr("class", "rule")
      .call(context.rule());

});

//
// Real-time downstream graphs
//
d3.select("#rt-downstream").call(function(div) {
	
	  div.append("div")
	      .attr("class", "axis")
	      .call(context.axis().orient("top"));
	
	  d3.json("query/endpoints/", function(endpoints) {
		  var metrics = [];
		  $.each(endpoints, function(i, endpoint) {
		  	metrics.push(create_metric(endpoint, 'throughput/received'));
		  });
		  
		  div.selectAll(".horizon")
		    .data(metrics)
		    .enter().append("div")
		    .attr("class", "horizon")
		    .call(context.horizon()
		    		.colors(["#006d2c","#31a354","#74c476","#bae4b3","#bdd7e7","#6baed6","#3182bd","#08519c"])
		    		.height(30)
		    		.extent([0, 100]));
	  });
	
	  div.append("div")
	      .attr("class", "rule")
	      .call(context.rule());
	
	});

//
// Real-time upstream graphs
//
d3.select("#rt-upstream").call(function(div) {
	
	  div.append("div")
	      .attr("class", "axis")
	      .call(context.axis().orient("top"));
	
	  d3.json("query/endpoints/", function(endpoints) {
		  var metrics = [];
		  $.each(endpoints, function(i, endpoint) {
		  	metrics.push(create_metric(endpoint, 'throughput/sent'));
		  });
		  
		  div.selectAll(".horizon")
		    .data(metrics)
		    .enter().append("div")
		    .attr("class", "horizon")
		    .call(context.horizon()
		    	    .colors(["#006d2c","#31a354","#74c476","#bae4b3","#bdd7e7","#6baed6","#3182bd","#08519c"])
		    		.height(30)
		    		.extent([0, 10]));
	  });
	
	  div.append("div")
	      .attr("class", "rule")
	      .call(context.rule());
	
	});

// On mousemove, reposition the chart values to match the rule.
context.on("focus", function(i) {
  d3.selectAll(".value").style("right", i == null ? null : context.size() - i + "px");
});




//====================================================================================
//                      A G G R E G A T E  P L O T S (circles)
//====================================================================================

var labelmap = {
	'bytessent': 'Upstream',
	'bytesreceived': 'Downstream',
};

var radius = 102, padding = 10;

var browns = ["#98abc5", "#8a89a6", "#7b6888", "#6b486b", "#a05d56", "#d0743c", "#ff8c00"];
var blues = ["#08519c","#3182bd","#6baed6","#bdd7e7","#bae4b3","#74c476","#31a354","#006d2c"];
var bluegreen = ["#3182bd","#31a354"];

var color = d3.scale.ordinal()
    .range(bluegreen);

var arc = d3.svg.arc()
    .outerRadius(radius)
    .innerRadius(radius - 30);

var pie = d3.layout.pie()
    .sort(null)
    .value(function(d) { return d.population; });

d3.json("query/throughput/"+(Date.now()-1e7)+"/"+Date.now(), function(error, data) {
  color.domain(d3.keys(data[0]).filter(function(key) { return key !== "endpoint"; }));

  data.forEach(function(d) {
    d.ages = color.domain().map(function(name) {
      return {name: name, population: +d[name]};
    });
  });

  var legend = d3.select("#summary-throughput").append("svg")
      .attr("class", "legend")
      .attr("width", radius * 2)
      .attr("height", radius * 2)
    .selectAll("g")
      .data(color.domain().slice().reverse())
    .enter().append("g")
      .attr("transform", function(d, i) { return "translate(0," + i * 20 + ")"; });

  legend.append("rect")
      .attr("width", 18)
      .attr("height", 18)
      .style("fill", color);

  legend.append("text")
      .attr("x", 24)
      .attr("y", 9)
      .attr("dy", ".35em")
      .text(function(d) { return labelmap[d]; });

  var svg = d3.select("#summary-throughput").selectAll(".pie")
      .data(data)
    .enter().append("svg")
      .attr("class", "pie")
      .attr("width", radius * 2)
      .attr("height", radius * 2)
    .append("g")
      .attr("transform", "translate(" + radius + "," + radius + ")");

  svg.selectAll(".arc")
      .data(function(d) { return pie(d.ages); })
    .enter().append("path")
      .attr("class", "arc")
      .attr("d", arc)
      .style("fill", function(d) { return color(d.data.name); });
  
  // Endpoint label	
  svg.append("text")
      .attr("dy", ".35em")
      .attr("font-size", "8pt")
      .attr("font-weight", "bold")
      .style("text-anchor", "middle")
      .text(function(d) { return d.endpoint; });
  
  // Upstream label
  svg.append("text")
      .attr("dy", "-1.7em")
      .style("text-anchor", "middle")
      .text(function(d) {
    	  return formatData(d.bytessent); 
      });
  
  // Downstream label
  svg.append("text")
      .attr("dy", "2.4em")
      .style("text-anchor", "middle")
      .text(function(d) {
          return formatData(d.bytesreceived); 
      });

});