import yaml

import matplotlib.pyplot as plt
import pandas as pd
from math import pi


f = open('config.yaml', 'r')
yaml_string = f.read()
parsed = yaml.load(yaml_string)

un_pivoted = []

skills_by_date = parsed['Skills_By_Date']
for date_dict in skills_by_date:
    date_value = {k: v for k, v in date_dict.items() if k == 'date'}['date']
    skills_list = {k: v for k, v in date_dict.items() if k == 'Skills'}['Skills']

    for k, v in skills_list.items():
        un_pivoted.append([date_value, k, v])

df = pd.DataFrame(un_pivoted, columns=['date', 'skill_name', 'skill_value'])
df = df.pivot(index='skill_name', columns='date', values='skill_value')

skill_name_list = list(df.index.values)
# print(skill_name_list)
N = len(skill_name_list)

values = df[df.columns[0]].values.tolist()
values += values[:1]

angles = [n / float(N) * 2 * pi for n in range(N)]
angles += angles[:1]

ax = plt.subplot(111, polar=True)
plt.xticks(angles[:-1], skill_name_list, color='grey', size=8)

ax.set_rlabel_position(0)
# plt.yticks()
# plt.ylim()

ax.plot(angles, values, linewidth=1, linestyle='solid')
ax.fill(angles, values, 'b', alpha=0.1)

plt.show()

# values = df.loc[0].drop('group').values.flatten().tolist()
# values += values [:1]
#
# angles =