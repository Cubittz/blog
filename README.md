# blog
Python multi user blog for Udacity Full Stack Web Developer Nanodegree

### 1. How to install and run
---------------

1. Download Google App Engine Console
2. Clone the repository from https://github.com/cubittz/blog.git
3. To run locally : 
	* Unzip the contents from the cloned directory and find the file _"app.yaml"_.
	* Open the app engine console and choose the option _"Add an existing application"_ from the Menu bar.
	* Navigate to the location where the repo was cloned.
	* Click the *_"Run"_* button and navigate to the port mentioned for the app in the app engine console. If this is the first time you're running the app you will have the site open at : localhost:8080

### 2. Directory Structure
--------------
```
-css
-templates
	-contains all the template(.html) files and a javascript file used for comments
-app.yaml
-index.yaml
-main.py
-README.md
```

### 3. Resources
-------
* Python is used as the scripting language for the server
* `jinja2`, a templating library for Python & natively implemented in Google App Engine
`webapp2`, GAE's main library
* `db` : The Google Datastore DB Client Library allows App Engine Python apps to connect to Cloud Datastore. 
* `hmac`, `hashlib` to enable encryption
* `re` to enable Regular Expression check for email and password inputs

* Front-end languages and frameworks : HTML, CSS, javascript, TinyMCE editor, Bootstrap

* App Engine : Google App Engine (GAE), Google's platform as a service solution
