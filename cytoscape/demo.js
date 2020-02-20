


function load_data(params) {
	
	var xhr = new XMLHttpRequest();
	
	var url = "http://127.0.0.1:5000/query";
	
	
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
	    }
	};
	
	show_info({status: "Performing the query"});
	xhr.send(params);
}

function load_graphml(params) {
	
	var xhr = new XMLHttpRequest();
	
	var url = "http://127.0.0.1:5000/graphml";
	
	
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
	                'background-color': '#666',
					content: ' data(label)'
	       		}
	       	},
	       	{
	            selector: 'edge',
	            style: {
	            	'width': 'data(weight)',
	                'line-color': '#999'
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
	                'background-color': '#666',
					content: ' data(name)'
	       		}
	       	},
	       	{
	            selector: 'edge',
	            style: {
	            	'width': 'data(weight)',
	                'line-color': '#999', 
	                'curve-style': 'bezier',
	                'content': 'data(label)',
	        		'target-arrow-shape': 'triangle',
	        		'target-arrow-color': '#999',
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
	var params = {};
	
	['endpoint', 'id', 'prefixes', 'nodes', 'links', 'limit', 'optimize'].forEach(function(st) {
		params[st] = document.getElementById(st).value.trim();
	});
	
	console.log(params);
	
	load_data(JSON.stringify(params));
}

function updateGraphml() {
	var params = {'format': 'graphml'};
	
	['endpoint', 'id', 'prefixes', 'nodes', 'links', 'limit', 'optimize'].forEach(function(st) {
		params[st] = document.getElementById(st).value.trim();
	});
	console.log("updateGraphml");
	console.log(params);
	
	load_graphml(JSON.stringify(params));
}
