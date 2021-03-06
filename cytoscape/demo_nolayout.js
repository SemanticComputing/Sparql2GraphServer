var GRAPH_SERVER = 'http://127.0.0.1:5000';
// or https://sparql-network.demo.seco.cs.aalto.fi

function load_data(params) {

	var xhr = new XMLHttpRequest();

	var url = GRAPH_SERVER + "/query";

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

// Start showing cytoscape view
function draw(elements) {
	for (var i=0; i<elements.nodes.length; i++){
		// console.log(elements.nodes[i].data['_x'])
		// console.log(elements.nodes[i].data['_x']*20.0)
		elements.nodes[i].position = {'x': elements.nodes[i].data['_x']*200.0, 
			'y': elements.nodes[i].data['_y']*200.0}
	}

	var cy = cytoscape({
        container: document.getElementById('network'),
		elements: elements,
		layout: { name: 'preset' },
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
	console.log(elements)
	for (var i=0; i<elements.nodes.length; i++){
		// console.log(elements.nodes[i].data['_x'])
		// console.log(elements.nodes[i].data['_x']*20.0)
		elements.nodes[i].position = {'x': elements.nodes[i].data['x']*400.0, 
			'y': elements.nodes[i].data['y']*400.0}
	}

	var cy = cytoscape({
        container: document.getElementById('network'),
		elements: elements,
		layout: { name: 'preset' },
		style: [
	        {
	            selector: 'node',
							style: {
	                "shape": 'ellipse',
							"height": ele => 5+50.*(ele.data('pagerank') || 0.001),
	      					"width": ele => 5+50.*(ele.data('pagerank') || 0.001),
							"text-valign": "center",
							"text-halign": "right",
	                		'background-color': ele => ele.data('color') || "#555",
							content: ele => " "+ ele.data('name') || ""
	       		}
	       	},
	       	{
	            selector: 'edge',
	            style: {
	            	'width': ele => 1, // ele.data('weight') || 1,
	                'line-color': '#999',
	                'curve-style': 'bezier',
	                'content': ele => ele.data('name') || "",
	        		// 'target-arrow-shape': 'triangle',
	        		// 'target-arrow-color': '#999',
	        		'color': '#555',
	        		'font-size': '9',
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
