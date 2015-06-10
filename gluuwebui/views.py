from gluuwebui import app
from flask import render_template, request, flash, redirect, url_for

import requests

api_base = app.config["API_SERVER_URL"]

@app.route("/")
def index():
    return render_template( "index.html" )

@app.route("/node")
def list_nodes():
    # TODO call the API and get the list
    return render_template( "entity_list.html", name="Nodes" )

@app.route("/provider", methods=['GET', 'POST'])
def list_providers():
    """ Render a web page that will have a list of providers and their details listed.
    So this fucntion has to call GET /provider and then using the returned result to 
    call /provider/<provider_id> for each id listed. Then pass the complete data to
    the template to render."""

    if request.method == "GET":
        # call the API and get the list
        provider_data = []
        r = requests.get(api_base+"provider")
        providers = r.json()
        for provider in providers:
            p = requests.get(api_base+"provider/"+provider['id'])
            provider_data.append( p.json() )
        return render_template("provider.html", data=provider_data )

    elif request.method == "POST":
        # TODO form validation as required
        payload = {"hostname" : request.form['hostname'], "docker_base_url" : request.form['docker_base_url']}
        r = requests.post(api_base+"provider", data=payload)
        if r.status_code != 201: # TODO improve response handling
            flash("Sorry the provider could not be added. API Server returned "+str(r.status_code), category="danger")
        else:
            flash("Provider successfully added with ID: "+r.json()['id'], category="success")
        return redirect(url_for('list_providers'))


@app.route("/cluster")
def list_clusters():
    # TODO call the API and get the list
    return render_template( "entity_list.html", name="Clusters" )
