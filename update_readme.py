import json
import re
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
myq_core = IntegrationInformation(name="My Q Core Integration", link="https://www.home-assistant.io/integrations/myq", domain="myq")
snoo_core = IntegrationInformation(name="Snoo Integration", link="https://www.home-assistant.io/integrations/snoo", domain="snoo")
snoo_custom = IntegrationInformation(name="Snoo Core Integration", link="https://github.com/Lash-L/snoo-hacs", domain="snoo")

follow_custom = {"roborock":roborock_custom}
follow_core = {"roborock": roborock_core, "anova":anova_core, "oralb":oralb_core, "myq": myq_core}
def get_custom_integration_information():
    data = requests.get("https://analytics.home-assistant.io/custom_integrations.json")
    json_data = data.json()
    return {key: json_data[key] for key in follow_custom.keys()}

def get_core_integration_information():
    data = requests.get("https://analytics.home-assistant.io/integrations/")
    text = data.text
    pattern = r'const tableEntries = (\[.*?\]);'
    matches = re.search(pattern, text, re.S)
    table_entries_str = matches.group(1)
    table_entries = json.loads(table_entries_str)
    pattern = r'\(([\d.]+)%\) installations have chosen'
    matches = re.search(pattern, text)
    percentage = float(matches.group(1)) / 100
    return [ entry for entry in table_entries if entry['domain'] in follow_core.keys()], percentage


def update_readme():
    core_update = get_core_integration_information()
    custom_update = get_custom_integration_information()
    for update in core_update[0]:
        follow_core[update['domain']].total = update['installations']
    for update_key, update in custom_update.items():
        follow_custom[update_key].total = update['total']
    for integration in list(follow_core.values()) + list(follow_custom.values()):
        integration.estimated = int(integration.total / core_update[1] * 3)
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

    readme_content[start_index + 1:end_index] = build_new_project_table()

    # Write the updated content back to the readme.md file
    with open('README.md', 'w') as file:
        file.writelines(readme_content)


def build_new_project_table():
    result = f"""
### Home Assistant (Updated as of {date.today()})

| Project | Lower bounds users | Upper bounds users |
| ------- | ------------------ | ------------------ |
"""
    for integration in list(follow_custom.values()) + list(follow_core.values()):
        result += f"| [{integration.name}]({integration.link}) | {integration.total} | {integration.estimated} |\n"
    return result

update_readme()
