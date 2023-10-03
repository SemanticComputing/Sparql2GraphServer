var GRAPH_SERVER = 'http://127.0.0.1:5000';
// or https://sparql-network.demo.seco.cs.aalto.fi

function load_data(params) {

	var xhr = new XMLHttpRequest();

	var url = GRAPH_SERVER + "/query_ego";

	xhr.open('POST', url, true);
	xhr.setRequestHeader('Content-type', 'application/json');

	xhr.onreadystatechange = function () {
	    if (xhr.status === 200) {
	    	if (xhr.readyState === 4) {
		        var res = JSON.parse(xhr.responseText);
		        console.log("OK", xhr, res);

		        //	draw(res.elements);
		        drawWithLabelTexts(res.elements);
		        show_info(res.metrics);
	     	}
	    } else {
		    show_info({status:"Query failed"});
			console.log("FAIL", xhr);
			console.log(params);
	    }
	};

	show_info({status: "Performing the query"});
	console.log(params);
	xhr.send(params);
}

function load_graphml(params) {

	var xhr = new XMLHttpRequest();

	var url = GRAPH_SERVER+"/graphml";

	xhr.open('POST', url, true);
	xhr.setRequestHeader('Content-type', 'application/json');

	xhr.onreadystatechange = function () {
	    if (xhr.status === 200) {
	    	if (xhr.readyState === 4) {
		        var res = xhr.responseText;
		        console.log("OK", xhr, res);

		        var elem = document.getElementById('network');
		        res = res.replace(/\</g,"&lt;").replace(/\>/g,"&gt;")
		        elem.innerHTML = res;

	     	}
	    } else {
		    show_info({status:"Query failed"});
	    	console.log("FAIL", xhr);
	    }
	};

	show_info({status: "Performing the query"});
	xhr.send(params);
}

function load_signature(params) {

	var xhr = new XMLHttpRequest();

	var url = GRAPH_SERVER+"/signature";

	xhr.open('POST', url, true);
	xhr.setRequestHeader('Content-type', 'application/json');

	xhr.onreadystatechange = function () {
	    if (xhr.status === 200) {
	    	if (xhr.readyState === 4) {
		        var res = xhr.responseText;
		        console.log("OK", xhr, res);

		        var elem = document.getElementById('network');
		        res = res.replace(/\</g,"&lt;").replace(/\>/g,"&gt;")
		        elem.innerHTML = res;

	     	}
	    } else {
		    show_info({status:"Query failed"});
	    	console.log("FAIL", xhr);
	    }
	};

	show_info({status: "Performing the query"});
	xhr.send(params);
}

class ValueScaler {
	a;
	b;
	constructor (low, high) {
	  this.low = low
	  this.high = high
	}
  
	fit (vals) {
	  const valmin = Math.min(...vals)
	  const valmax = Math.max(...vals)
	  if (valmax === valmin) {
		this.a = 0.0
	  } else {
		this.a = (this.high - this.low) / (valmax - valmin)
	  }
	  this.b = this.low - valmin * this.a
	}
  
	transform (vals) {
	  return vals.map(x => { return x * this.a + this.b })
	}
  
	fitTransform (vals) {
	  this.fit(vals)
	  return this.transform(vals)
	}
  }


class ColorScaler extends ValueScaler {
	col1;
	col2;
	constructor (low, high) {
	  super(0.0, 1.0)
	  this.col1 = low
	  this.col2 = high
	}
  
	// super.fit(vals)
  
	_process (s0, s1, r) {
	  const x0 = parseInt(s0)
	  const x1 = parseInt(s1)
	  if (isNaN(x0) || isNaN(x1)) return s0
	  return Math.floor(x0 + (x1 - x0) * r)
	}
  
	transform (vals) {
	  const s1 = this.col1.split(/(\d+)/)
	  const s2 = this.col2.split(/(\d+)/)
	  const _vals01 = vals.map(x => { return x * this.a + this.b })
  
	  return _vals01.map(v => s1.map((s, i) => this._process(s, s2[i], v)).join(''))
	}
  }
  
// Start showing cytoscape view
function draw(elements) {

	var cy = cytoscape({
        container: document.getElementById('network'),
        elements: elements,
		layout: {
			name: 'cose',
			idealEdgeLength: 100,
			nodeOverlap: 20,
			refresh: 20,
			fit: true,
			padding: 30,
			randomize: false,
			componentSpacing: 100,
			nodeRepulsion: 400000,
			edgeElasticity: 100,
			nestingFactor: 5,
			gravity: 80,
			numIter: 1000,
			initialTemp: 200,
			coolingFactor: 0.95,
			minTemp: 1.0
		},
		style: [
	        {
	            selector: 'node',
	            style: {
	                "shape": 'ellipse',
					"height": '16px',
	      			"width": '16px',
					"text-valign": "center",
					"text-halign": "right",
	                'background-color': 'red',
					content: ' data(label)'
	       		}
	       	},
	       	{
	            selector: 'edge',
	            style: {
	            	'width': 'data(weight)',
	              'line-color': '#C0FFEE',
		            content: ' data(name) ',
		            // 'target-arrow-shape': 'triangle',
		            // 'target-arrow-color': '#999',
		            color: '#555',
		            'font-size': '6',
		            'text-valign': 'top',
		            'text-halign': 'center'
	            }
	        }
	        ]
		});
	};


function drawWithLabelTexts(elements) {
	// nodes
	console.log(elements.nodes)

	let arr = elements.nodes.map(ele => Math.sqrt(ele.data.out_degree) || 0)
	let res = (new ValueScaler(10.0, 35.0)).fitTransform(arr)
  	elements.nodes.forEach((ele, i) => { ele.data.size = res[i] })

	arr = elements.nodes.map(ele => ele.data.distance || 0)
	res = (new ColorScaler('rgb(255, 0, 0)', 'rgb(0, 0, 255)')).fitTransform(arr)
	elements.nodes.forEach((ele, i) => { ele.data.color = res[i] })

	//  edge width
	arr = elements.edges.map(ele => ele.data.weight || 1)
	res = (new ValueScaler(1.0, 6.0)).fitTransform(arr)
	elements.edges.forEach((ele, i) => { ele.data.weight = res[i] })

	var cy = cytoscape({
        container: document.getElementById('network'),
        elements: elements,
		layout: {
			name: 'cose',
			idealEdgeLength: 100,
			nodeOverlap: 20,
			refresh: 20,
			fit: true,
			padding: 30,
			randomize: false,
			componentSpacing: 100,
			nodeRepulsion: 400000,
			edgeElasticity: 100,
			nestingFactor: 5,
			gravity: 80,
			numIter: 1000,
			initialTemp: 200,
			coolingFactor: 0.95,
			minTemp: 1.0
		},
		style: [
	        {
	            selector: 'node', // 'node[image]',
							style: {
	                		"shape": 'ellipse',
							"height": ele => ele.data('size'),
	      					"width": ele => ele.data('size'),
							// "height": ele => 3+100*(ele.data('pagerank') || 1),
	      					// "width": ele => 3+100*(ele.data('pagerank') || 1),
							"text-valign": "center",
							"text-halign": "right",
	                		'background-color': ele => ele.data('color') || "#555",
							'border-width': ele => (ele.data('distance')<1 ? 2 : 0),
							'border-color': 'black',
							// 'background-image': ele => ele.data('image') || "",
							content: ele => " "+ ele.data('name') || ""

	       		}
	       	},
	       	{
	            selector: 'edge',
	            style: {
	            	'width': ele => ele.data('weight') || 1,
	                'line-color': '#999',
	                'curve-style': 'bezier',
	                'content': ele => ele.data('label') || "-",
	        		'target-arrow-shape': 'triangle',
	        		// 'target-arrow-color': '#999',
	        		'color': '#555',
	        		'font-size': '11',
	        		"text-valign": "top",
	        		"text-halign": "center",
	        		'edge-text-rotation': 'autorotate',
	        		"text-background-opacity": 1,
	        		"text-background-color": "#FFF",
	        		"text-background-shape": "roundrectangle"
	            }
	        }
	        ]
		}
	);
};

function show_info(data) {
	var st="",
		elem = document.getElementById('info');
	for (n in data) {
		st += n +": "+data[n] + ", ";
	}
	elem.innerHTML = st;
}

function update() {
	console.log('Updating')
	var params = {customHttpHeaders: {
									//	for wikidata queries:
									"User-Agent": "OpenAnything/1.0 +http://diveintopython.org/http_web_services/"}
									};
	// params = {}
								
	var srv = document.getElementById("server");
	if (srv && srv.value) {
		GRAPH_SERVER = srv.value;
	}
	
	var auth = document.getElementById("Authorization");
	if (auth && auth.value) {
		params.customHttpHeaders.Authorization = auth.value.trim();
	}
	
	['endpoint', 'id', 'prefixes', 'nodes', 'links', 'limit', 'optimize'].forEach(function(st) {
		params[st] = document.getElementById(st).value.trim();
	});

	console.log(params);

	load_data(JSON.stringify(params));
}

function updateGraphml() {
	console.log('Loading Graphml')
	var params = {customHttpHeaders: {
									//	for wikidata queries:
									"User-Agent": "OpenAnything/1.0 +http://diveintopython.org/http_web_services/"}
									};
								
	var srv = document.getElementById("server");
	if (srv && srv.value) {
		GRAPH_SERVER = srv.value;
	}
	
	var auth = document.getElementById("Authorization");
	if (auth && auth.value) {
		params.customHttpHeaders.Authorization = auth.value.trim();
	}
	
	['endpoint', 'id', 'prefixes', 'nodes', 'links', 'limit', 'optimize'].forEach(function(st) {
		params[st] = document.getElementById(st).value.trim();
	});

	console.log(params);

	load_graphml(JSON.stringify(params));
}


function updateSignature() {
	console.log('Loading Signature')
	var params = {customHttpHeaders: {
									//	for wikidata queries:
									"User-Agent": "OpenAnything/1.0 +http://diveintopython.org/http_web_services/"}
									};
								
	var srv = document.getElementById("server");
	if (srv && srv.value) {
		GRAPH_SERVER = srv.value;
	}
	
	var auth = document.getElementById("Authorization");
	if (auth && auth.value) {
		params.customHttpHeaders.Authorization = auth.value.trim();
	}
	
	['endpoint', 'id', 'prefixes', 'nodes', 'links', 'limit', 'optimize'].forEach(function(st) {
		params[st] = document.getElementById(st).value.trim();
	});

	console.log(params);

	load_signature(JSON.stringify(params));
}
