import hashlib
import os
from dataclasses import dataclass
from datetime import date

import requests


@dataclass
class IntegrationInformation:
    name: str
    link: str
    domain: str
    total: int = 0
    estimated: int = 0

roborock_custom = IntegrationInformation(name="Roborock Custom Integration", link="https://github.com/humbertogontijo/homeassistant-roborock", domain="roborock")
roborock_core = IntegrationInformation(name="Roborock Core Integration", link="https://www.home-assistant.io/integrations/roborock", domain="roborock")
anova_core = IntegrationInformation(name="Anova Core Integration", link="https://www.home-assistant.io/integrations/anova", domain="anova")
oralb_core = IntegrationInformation(name="Oral-B Core Integration", link="https://www.home-assistant.io/integrations/oralb", domain="oralb")
snoo_core = IntegrationInformation(name="Snoo Core Integration", link="https://www.home-assistant.io/integrations/snoo", domain="snoo")
snoo_custom = IntegrationInformation(name="Snoo HACS Integration", link="https://github.com/Lash-L/snoo-hacs", domain="snoo")
harbor_core = IntegrationInformation(name="Harbor Sleep Core Integration", link="https://www.home-assistant.io/integrations/harbor", domain="harbor")

LOCAL_SERVER_REPO = "Python-roborock/local_roborock_server"
LOCAL_SERVER_LINK = f"https://github.com/{LOCAL_SERVER_REPO}"


def app_slug(repository_url, slug):
    # Supervisor prefixes third party app slugs with the first 8 chars of sha1(repository url)
    return f"{hashlib.sha1(repository_url.lower().encode()).hexdigest()[:8]}_{slug}"


local_server_app = IntegrationInformation(name="Roborock Local Server App", link=LOCAL_SERVER_LINK, domain=app_slug(LOCAL_SERVER_LINK, "roborock_local_server"))

follow_custom = {"roborock":roborock_custom, "snoo": snoo_custom}
follow_core = {"roborock": roborock_core, "anova":anova_core, "oralb":oralb_core, "snoo": snoo_core, "harbor": harbor_core}
follow_apps = {local_server_app.domain: local_server_app}
def get_custom_integration_information():
    data = requests.get("https://analytics.home-assistant.io/custom_integrations.json")
    json_data = data.json()
    return {key: json_data[key] for key in follow_custom.keys()}

def get_core_integration_information():
    data = requests.get("https://analytics.home-assistant.io/current_data.json")
    json_data = data.json()
    integrations = json_data['integrations']
    reports_integrations = json_data['reports_integrations']
    active_installations = json_data['active_installations']
    percentage = reports_integrations / active_installations if active_installations else 1
    # Only OS and Supervised installs can run apps, so measure app reporting against those
    installation_types = json_data['installation_types']
    app_capable = installation_types['os'] + installation_types['supervised']
    app_percentage = json_data['reports_addons'] / app_capable if app_capable else 1
    table_entries = [
        {'domain': domain, 'installations': integrations[domain]}
        for domain in follow_core
        if domain in integrations
    ]
    return table_entries, percentage, app_percentage


def get_app_information():
    data = requests.get("https://analytics.home-assistant.io/addons.json")
    json_data = data.json()
    return {key: json_data[key] for key in follow_apps if key in json_data}


def get_github_stars(repository):
    headers = {"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}"} if os.environ.get("GITHUB_TOKEN") else {}
    data = requests.get(f"https://api.github.com/repos/{repository}", headers=headers)
    return data.json()['stargazers_count']


def update_readme():
    core_update = get_core_integration_information()
    custom_update = get_custom_integration_information()
    app_update = get_app_information()
    for update in core_update[0]:
        follow_core[update['domain']].total = update['installations']
    for update_key, update in custom_update.items():
        follow_custom[update_key].total = update['total']
    for update_key, update in app_update.items():
        follow_apps[update_key].total = update['total']
    for integration in list(follow_core.values()) + list(follow_custom.values()):
        integration.estimated = int(integration.total / core_update[1] * 3)
    for app in follow_apps.values():
        app.estimated = int(app.total / core_update[2] * 3)
    local_server_stars = get_github_stars(LOCAL_SERVER_REPO)
    with open('README.md', 'r') as file:
        readme_content = file.readlines()

    # Find the start and end indexes of the projects table
    start_index = None
    end_index = None
    for i, line in enumerate(readme_content):
        if line.strip() == "<!-- Projects-START -->":
            start_index = i
        elif line.strip() == "<!-- Projects-END -->":
            end_index = i

    readme_content[start_index + 1:end_index] = build_new_project_table(local_server_stars)

    # Write the updated content back to the readme.md file
    with open('README.md', 'w') as file:
        file.writelines(readme_content)


def build_new_project_table(local_server_stars):
    result = f"""
### Home Assistant (Updated as of {date.today()})

| Project | Lower bounds users | Upper bounds users |
| ------- | ------------------ | ------------------ |
"""
    for integration in list(follow_custom.values()) + list(follow_core.values()) + list(follow_apps.values()):
        result += f"| [{integration.name}]({integration.link}) | {integration.total} | {integration.estimated} |\n"
    result += f"""
[Roborock Local Server]({LOCAL_SERVER_LINK}) also has ⭐ {local_server_stars} stars on GitHub. Its row above only counts
the Home Assistant app, so anyone running the standalone Docker image isn't included.
"""
    return result

update_readme()
