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

	var cy = cytoscape({
        container: document.getElementById('network'),
        elements: elements,
		layout: {
			name: 'cose',
			idealEdgeLength: 150,
			nodeOverlap: 20,
			refresh: 20,
			fit: true,
			padding: 30,
			randomize: false,
			componentSpacing: 150,
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
							"height": ele => ele.data('size') || 12,
	      					"width": ele => ele.data('size') || 12,
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
