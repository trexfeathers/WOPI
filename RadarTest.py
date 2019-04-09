# Generates a radar chart of python skills, grouped by time, based on the content of config.yaml
# Radar chart code based on https://python-graph-gallery.com/390-basic-radar-chart/

import yaml
import matplotlib.pyplot as plt
import pandas as pd
from math import pi

# Read YAML content from the config file.
f = open('config.yaml', 'r')
yaml_string = f.read()
parsed = yaml.load(yaml_string)
f.close()

# Extract the data from the YAML structure into an un-pivoted list of dates and skill levels.
un_pivoted = []
skills_by_date = parsed['Skills_By_Date']
for date_dict in skills_by_date:
    date_value = {k: v for k, v in date_dict.items() if k == 'date'}['date']
    skills_list = {k: v for k, v in date_dict.items() if k == 'Skills'}['Skills']

    for k, v in skills_list.items():
        un_pivoted.append([date_value, k, v])

# Convert the un-pivoted data into a Pandas dataframe
df = pd.DataFrame(un_pivoted, columns=['date', 'skill_name', 'skill_value'])
min_skill = min(df['skill_value'])
max_skill = max(df['skill_value'])

# Pivot the dataframe into a table of skill names (rows) and dates (columns).
# If a skill is missing from any of the dates, replace the null value with a zero and adjust min_skill accordingly.
df = df.pivot(index='skill_name', columns='date', values='skill_value')
if df.isna().values.any():
    min_skill = min(1, min_skill)
    df.fillna(0, inplace=True)

# Get a list of skill names and count them.
skill_name_list = list(df.index.values)
N = len(skill_name_list)

# Create the radar chart without any data.
ax = plt.subplot(111, polar=True)

# Use the number of different skills to set the angles for each 'limb' (xtick) on the radar chart.
angles = [n / float(N) * 2 * pi for n in range(N)]
angles += angles[:1]        # need to complete the polygon by plotting back to the first point again.
plt.xticks(angles[:-1], skill_name_list, color='grey', size=8)

# Add y axis ticks to one of the radar chart limbs.
ax.set_rlabel_position(0)
plt.yticks(range(min_skill, max_skill+1), color='grey', size=7)
plt.ylim(min_skill-1, max_skill+1)

# Plot one polygon for each date in the dataframe.
for label, content in df.iteritems():
    # without .tolist(), the 'list' seems to contain more than expected - type ndarray instead of list
    values = content.tolist()
    values += values[:1]        # Need to complete the polygon by plotting back to the first point again.

    ax.plot(angles, values, linewidth=1, linestyle='solid', label=label)
    ax.fill(angles, values, alpha=0.3)

# Display the completed chart.
plt.legend(loc='lower right', bbox_to_anchor=(1, 1))
plt.show()