# Generates a radar chart of python skills, grouped by time, based on the content of config.yaml
# Radar chart code based on https://python-graph-gallery.com/390-basic-radar-chart/

import argparse
import logging
import sys
import yaml

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd

from math import pi


def print_smart(string, print_type):
    logging.basicConfig(level=logging.WARNING)
    log = logging.getLogger('RadarTest')

    if print_type == 2:     # success
        print('\033[;32m' + string + '\033[m')
    elif print_type == 3:   # error
        log.error('\n\033[;31m' + string + '\033[m')    # outputs as stderr
    else:
        print(string)


def radar_chart(config_path, save_path=''):
    # Read YAML content from the config file.
    if config_path[-5:] != '.yaml':
        print_smart('Config file extension is not ".yaml". Chart will not be plotted', 3)
        return

    with open(config_path, 'r') as f:
        yaml_string = f.read()

    parsed = yaml.load(yaml_string)

    # missing_keys = {
    #     'Chart Title': 'Config "Chart Title" key missing/invalid. No title will be displayed',
    #     'Chart Size': 'Config "Chart Size" key missing/invalid. Default size will be used',
    #     'Color Hex': 'Config "Color Hex" key missing/invalid on some date(s). Default colours used in these cases'
    # }

    # Extract the data from the YAML structure into an un-pivoted list of dates and skill levels.
    un_pivoted = []
    color_dict = {}
    skills_by_date = parsed['Skills_By_Date']
    for date_dict in skills_by_date:
        date_value = date_dict['Date'].strftime('%Y-%m-%d')
        color_value = date_dict.get('Color Hex', 'default')
        skills_list = date_dict['Skills']

        color_dict[date_value] = color_value

        for k, v in skills_list.items():
            un_pivoted.append([date_value, k, v])

    # Convert the un-pivoted data into a Pandas DataFrame
    df = pd.DataFrame(un_pivoted, columns=['date', 'skill_name', 'skill_value'])
    df.sort_values(['date', 'skill_name'], inplace=True)
    min_skill = min(df['skill_value'])
    max_skill = max(df['skill_value'])

    # Pivot the DataFrame into a table of skill names (rows) and dates (columns).
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
    fig = ax.figure
    # fig.set_size_inches(1, 1)

    # Use the number of different skills to set the angles for each 'limb' (xtick) on the radar chart.
    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]        # need to complete the polygon by plotting back to the first point again.
    plt.xticks(angles[:-1], skill_name_list, color='grey', size=8)

    # Add y axis ticks to one of the radar chart limbs.
    ax.set_rlabel_position(0)
    plt.yticks(range(min_skill, max_skill+1), color='grey', size=7)
    plt.ylim(min_skill-1, max_skill+1)

    # Plot one polygon for each date in the DataFrame.
    for label, content in df.items():
        # without .tolist(), the 'list' seems to contain more than expected - type ndarray instead of list
        values = content.tolist()
        values += values[:1]        # Need to complete the polygon by plotting back to the first point again.

        plot_color = color_dict[label]

        try:
            ax.plot(angles, values, linewidth=1, linestyle='solid', label=label, color=plot_color)
            ax.fill(angles, values, alpha=0.3, color=plot_color)
        except:
            ax.plot(angles, values, linewidth=1, linestyle='solid', label=label)
            ax.fill(angles, values, alpha=0.3)
            print('Config "Color Hex" key missing/invalid on some date(s). Default colours used in these cases')

    try:
        plt.title(parsed['Chart Title'])
    except KeyError:
        print('Config "Chart Title" key missing/invalid. No title will be displayed')

    try:
        chart_size = parsed['Chart Size']
        chart_width = chart_size['Width']
        chart_height = chart_size['Height']
        fig.set_size_inches(chart_width, chart_height)
    except (KeyError, ValueError):
        print('Config "Chart Size" key missing/invalid. Default size will be used')

    # Display the completed chart.
    plt.legend(bbox_to_anchor=(0., -.15, 1., .102), loc=3,
               ncol=2, mode="expand", borderaxespad=0., fontsize=8)
    if save_path is not None:
        try:
            plt.savefig(fname=save_path)
            print_smart('Figure saved to:  ' + save_path, 2)
        except (FileNotFoundError, ValueError) as exception_:
            print_smart('Error when saving figure, displaying instead \nError message: \n\t' + str(exception_), 3)
            plt.show()
    else:
        plt.show()


def main():
    cmd_text = 'script to plot progress in Python skills, input via the config file'
    parser = argparse.ArgumentParser(description=cmd_text)
    parser.add_argument('-c', '--config',
                        help='Input path of config YAML file',
                        action='store',
                        required=True)
    parser.add_argument('-s', '--save',
                        help=
                        'Input save path INCLUDING file extension'
                        'If no valid path is provided, chart will be displayed instead',
                        action='store',
                        required=False)
    parser.add_argument('-e', '--example',
                        help='Display example of expected config file format',
                        action='store_true',
                        required=False)
    args = parser.parse_args()

    if args.example:
        print('''
            Please format the config file in line with the following example.
            All of the values can be changed, but the only keys that can change are the skill names.
            Save with the ".yaml" extension
            
            Chart Title: 'Martin Yeo Python Skill Progression'
            Skills_By_Date:
              - Date    : 2019-04-08
                Skills  :
                  'Skill 1' : 2
                  'Skill 2' : 5
    
              - Date    : 2019-04-12
                Skills  :
                  'Skill 1' : 3
                  'Skill 2' : 5
                  'Skill 5' : 4
          ''')
    else:
        # Radar_Chart(args.config, args.save)
        radar_chart(args.config, args.save)

main()