import requests
import json
from create_stack import Config


#  Appends prefix to title and all occurrences of "measurement" value in the Grafana JSON file
def __add_prefix_to_grafana_json(grafana_json, prefix):
    grafana_json["dashboard"]["title"] = prefix + ' ' + grafana_json["dashboard"]["title"]
    if 'panels' in grafana_json["dashboard"]:
        for i in grafana_json["dashboard"]['panels']:
            for j in i:
                if 'targets' in j:
                    for k in i['targets']:
                        if 'measurement' in k:
                            k['measurement'] = prefix + '_' + k['measurement']


def __add_prefix_to_grafana_loki_source_job(grafana_json, prefix):
    if 'panels' in grafana_json["dashboard"]:
        for i in grafana_json["dashboard"]['panels']:
            if i['datasource'] == 'Loki':
                for j in i['targets']:
                    j['expr'] = '{job="' + prefix + '_' + 'jmeter"}'


# add instances_required field to Grafana JSON under Number of Users
def __add_users_req_to_grafana_json(grafana_json, instances_required):
    for i in grafana_json["dashboard"]['panels']:
        for j in i:
            if 'targets' in j:
                for k in i['targets']:
                    if "alias" in k and k["alias"] == "Number of Users":
                        k["select"][0][1]["params"][0] = "*" + str(instances_required)


def __modify_dashboard_info_bar(grafana_json, total_users, duration, endpoint_url):
    if "options" in grafana_json["dashboard"]['panels'][0]:
        if "content" in grafana_json["dashboard"]['panels'][0]["options"]:
            grafana_json["dashboard"]['panels'][0]["options"][
                "content"] = "<p style=\"background-color:green;\" style=\"text-align:left;\">The endpoint for this run is: \n%s. Total users are %s. Duration of test is %s seconds  </p>    " \
                             % (endpoint_url, total_users, duration)


# responsible for posting the dashboard to Grafana and returning the URL to it
def __post_grafana_dash(config):
    key = config.grafana_key
    grafana_template = './' + config.test_directory + '/' + config.grafana_file
    prefix = config.prefix
    grafana_url = config.grafana_url
    instances_required = config.instances_required
    total_users = config.total_users
    duration = config.duration
    endpoint_url = config.icap_endpoint_url

    if grafana_url[len(grafana_url) - 1] != '/':
        grafana_url += '/'
    if not grafana_url.startswith("http"):
        grafana_url = "http://" + grafana_url

    grafana_api_url = grafana_url + 'api/dashboards/db'

    headers = {
        "Authorization": "Bearer " + key,
        "Content-Type": "application/json"}

    with open(grafana_template) as json_file:
        grafana_json = json.load(json_file)
        __add_users_req_to_grafana_json(grafana_json, instances_required)
        __add_prefix_to_grafana_json(grafana_json, prefix)
        __modify_dashboard_info_bar(grafana_json, total_users, duration, endpoint_url)
        __add_prefix_to_grafana_loki_source_job(grafana_json, prefix)

    resp = requests.post(grafana_api_url, json=grafana_json, headers=headers)
    d = eval(resp.text)
    # if the response contains a URL, use it to build a url that links directly to the newly created dashboard
    if "url" in d:
        return grafana_url + d.get('url')
    else:
        print("Dashboard creation failed: {0}".format(resp.text))


def main(config):
    created_dashboard_url = __post_grafana_dash(config)

    if created_dashboard_url:
        print("Dashboard created at: ")
        print(created_dashboard_url)


# main: Gets command line arguments, creates dashboard in grafana, outputs URL in response (if any)
if __name__ == '__main__':
    main(Config)
