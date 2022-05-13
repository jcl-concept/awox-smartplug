(function() {
	class ExampleAddon1 extends window.Extension {
	    constructor() {
	      	super('example-addon1');
      		
            this.debug = false; // if enabled, show more output in the console
            
			console.log("Adding example-addon1 addon to main menu");
			this.addMenuEntry('Example addon 1');
            
            // Load the html
            this.content = ''; // The html from the view will be loaded into this
			fetch(`/extensions/${this.id}/views/content.html`)
	        .then((res) => res.text())
	        .then((text) => {
	         	this.content = text;
                
                // This is needed because the user might already be on the addon page and click on the menu item again. This helps to reload it.
	  		 	if( document.location.href.endsWith("extensions/example-addon1") ){
	  		  		this.show();
	  		  	}
	        })
	        .catch((e) => console.error('Failed to fetch content:', e));
            
            
            // This is not needed, but might be interesting to see. It will show you the API that the controller has available. For example, you can get a list of all the things this way.
            console.log("window API: ", window.API);

            
	    }



		
        
        
        // This is called then the user clicks on the addon in the main menu, or when the page loads and is already on this addon's location.
	    show() {
			console.log("example-addon1 show called");
			console.log("this.content:");
			console.log(this.content);
            
            
			const main_view = document.getElementById('extension-example-addon1-view');
			
			if(this.content == ''){
                console.log("content has not loaded yet");
				return;
			}
			else{
				main_view.innerHTML = this.content;
			}
			
            
            
            
            // First button press
			document.getElementById('extension-example-addon1-first-button').addEventListener('click', (event) => {
				console.log("first button clicked. Event: ", event);
                
                const first_value = document.getElementById('extension-example-addon1-first-value-input').value;
                
                if(first_value != ""){
    				window.API.postJson(
    					`/extensions/${this.id}/api/ajax`,
    					{'action':'save_first_value', 'value':first_value}
                        
    				).then((body) => {
                        console.log("save response: ", body);
                        if(body.state == true){
                            console.log("saved ok");
                            document.getElementById('extension-example-addon1-first-value-input').value = "";
                        }
                        
    				}).catch((e) => {
    					console.log("example-addon1: connnection error after first button press: ", e);
    				});
                    
                }
                else{
                    alert("Please provide a longer value");
                }
                
			});
			
            
            
            
            
            
            // Easter egg when clicking on the title
			document.getElementById('extension-example-addon1-title').addEventListener('click', (event) => {
				console.log("easter egg!");
			});
            
            
            
            
            // Button to show the second page
            document.getElementById('extension-example-addon1-show-second-page-button').addEventListener('click', (event) => {
                document.getElementById('extension-example-addon1-content-container').classList.add('extension-example-addon1-showing-second-page');
			});
            
            // Back button, shows main page
            document.getElementById('extension-example-addon1-back-button').addEventListener('click', (event) => {
                document.getElementById('extension-example-addon1-content-container').classList.remove('extension-example-addon1-showing-second-page');
                
                this.get_init_data(); // repopulate the main page
                
			});
            
            
            // Finally, request the first data from the addon's API
            this.get_init_data();
		}
		
	
		// This is called then the user navigates away from the addon. It's an opportunity to do some cleanup. To remove the HTML, for example, or stop running intervals.
		hide() {
			console.log("example-addon1 hide called");
		}
        
    
    
        // This gets the first data from the addon API
        get_init_data(){
            
			try{
				
		  		// Init
		        window.API.postJson(
		          `/extensions/${this.id}/api/ajax`,
                    {'action':'init'}

		        ).then((body) => {
                    console.oog("init response: ", body);
                    
                    // We have now received initial data from the addon, so we can hide the loading spinner by adding the 'hidden' class to it.
                    
                    document.getElementById('extension-example-addon1-loading').classList.add('extension-example-addon1-hidden');
                    
                    if(typeof body.debug != 'undefined'){
                        this.debug = body.debug;
                        if(body.debug == true){
                            console.log("example addon 1: debugging enabled. Init API result: ", body);
                            
                            // If debugging is enabled, please show a big warning that this is the case. Debugging can be a privacy risk, since lots of data will be stored in the internal logs. Showing this warning helps avoid abuse.
                            if(document.getElementById('extension-example-addon1-debug-warning') != null){
                                document.getElementById('extension-example-addon1-debug-warning').style.display = 'block';
                            }
                        }
                    }
                    
                    // get a value from the response and store it
                    if(typeof body.a_number_setting != 'undefined'){
                        this.a_number_setting = body['a_number_setting'];
                        console.log("this.a_number_setting: ", this.a_number_setting);
                    }
				
		        }).catch((e) => {
		  			console.log("Error getting ExampleAddon1 init data: ", e);
		        });	

			}
			catch(e){
				console.log("Error in API call to init: ", e);
			}
        }
    

        
        
    
	
		//
		//  REGENERATE ITEMS LIST ON MAIN PAGE
		//
	
		regenerate_items(items, page){
            // This funcion takes a list of items and generates HTML from that, and places it in the list container on the main page
			try {
				console.log("regenerating. items: ", items);
		        if(this.debug){
		            console.log("I am only here because debugging is enabled");
		        }
                
                let list_el = document.getElementById('extension-example-addon1-main-items-list');
                if(list_el == null){
                    console.log("Error, the main list container did not exist yet");
                    return;
                }
                
                // If the items list does not contain actual items, then stop
                if(items.length == 0){
                    list.innerHTML = "No items";
                    return
                }
                else{
                    list.innerHTML = "";
                }
                
                // The original item which we'll clone  for each item that is needed in the list.  This makes it easier to design each item.
				const original = document.getElementById('extension-example-addon1-original-item');
			    //console.log("original: ", original);
                
			    // Since each item has a name, here we're sorting the list based on that name first
				items.sort((a, b) => (a.name.toLowerCase() > b.name.toLowerCase()) ? 1 : -1)
				
                
				// Loop over all items in the list
				for( var item in items ){
					
					var clone = original.cloneNode(true); // Clone the original item
					clone.removeAttribute('id'); // Remove the ID from the clone
                    
                    // Place the name in the clone
                    clone.getElementsByClassName("extension-example-addon1-item-name")[0].innerText = items[item].name; // The original and its clones use classnames to avoid having the same ID twice
                    
                    // You could add a specific CSS class to an element depending on some value
                    //clone.classList.add('extension-example-addon1-item-highlighted');   
                    

					// DELETE button
					const delete_button = clone.querySelectorAll('.extension-example-addon1-item-delete-button')[0];
                    console.log("delete button element: ", delete_button);
                    delete_button.setAttribute('data-name', items[item].name);
                    
					delete_button.addEventListener('click', (event) => {
                        console.log("delete button click. event: ", event);
                        if(confirm("Are you sure you want to delete this item?")){
    						
    						// Inform backend
    						window.API.postJson(
    							`/extensions/${this.id}/api/ajax`,
    							{'action':'delete','name': event.target.dataset.name}
    						).then((body) => { 
    							console.log("delete item response: ", body);
                                if(body.state == true){
                                    // Remove the item form the list, or regenerate the entire list instead
                                    //parent4.removeChild(parent3);
                                }

    						}).catch((e) => {
    							console.log("example-addon1: error in delete items handler: ", e);
    						});
                        }
				  	});

                    // Add the clone to the list container
					list.append(clone);
                    
                    
                    
				} // end of for loop
                
            
            
			}
			catch (e) {
				console.log("Error in regenerate_items: ", e);
			}
		}
	
 
    
    }

	new ExampleAddon1();
	
})();


