# Generates a radar chart of python skills, grouped by time, based on the content of config.yaml
# Radar chart code based on https://python-graph-gallery.com/390-basic-radar-chart/

import argparse
import logging
import os
import yaml

import matplotlib.pyplot as plt
import matplotlib.colors as mpl_colors
import pandas as pd

from math import pi

'''
tests I would like:
Normal Behaviour
  - Add skill
  - Change skill name
  - Change skill value
  - Change chart title
  - Change chart dimensions
  - Save / display chart
  - Float vs integer skill values
  - Add date
  - Change date
  - Sort dates
  - Sort skills
  - Non-numeric skill values

Critical errors
  - neither -c or -e arguments passed  
  - Invalid -c file path
  - Invalid YAML format
  - Config missing mandatory fields

Non-critical errors  
  - Invalid -s file path
  - Un-supported -s file extension
  - Missing colour(s)
  - Missing chart title
  - Missing chart dimensions
  
'''


def print_success_error(string, is_success=False):
    # Enhancements over the standard print(), showing green for success and red for error.
    # Errors use the logging module to output as stderr and be added to the logs.

    logging.basicConfig(level=logging.ERROR)
    formatter = logging.Formatter('%(asctime)s %(message)s')

    file_handler = logging.FileHandler('radar_errors.log')
    file_handler.setFormatter(formatter)

    log = logging.getLogger('RadarTest')
    log.addHandler(file_handler)

    if is_success:     # success
        print('\033[;32m' + string + '\033[m')
    elif not is_success:   # error
        log.error('\n\033[;31m' + string + '\033[m\n')    # outputs as stderr
    else:
        print(string)


def radar_chart(config_yaml, save_path=''):
    # Generates the radar chart based on the content of the config file.

    # # Check that the config file exists, and read content from it.
    # if os.path.isfile(config_path):
    #     with open(config_path, 'r') as f:
    #         yaml_string = f.read()
    # else:
    #     print_success_error('Invalid config path provided. Chart will not be plotted', is_success=False)
    #     return

    # Attempt to parse the config file content as YAML content.
    try:
        parsed = yaml.load(config_yaml)
    except yaml.scanner.ScannerError as exception_:
        print_success_error('Invalid YAML format in config file. Chart will not be plotted \nError message: \n\n' +
                            str(exception_), is_success=False)
        return

    # Search YAML top level for "Skills By Date", which contains the core information.
    skills_by_date = None
    if 'Skills By Date' in parsed:
        skills_by_date = parsed['Skills By Date']
    if type(skills_by_date) is not list:
        print_success_error('Config "Skills By Date" key missing/invalid. Chart will not be plotted', is_success=False)
        return

    # Extract the data from the YAML structure into an un-pivoted list of dates and skill levels.
    un_pivoted = []
    color_dict = {}
    for index_, date_dict in enumerate(skills_by_date):
        date_value = None       # date_value needs to be reset as it is used for rollback in case of an exception.

        try:
            date_value = date_dict['Date'].strftime('%Y-%m-%d')
            skills_list = date_dict['Skills']

            # Supplying a colour for the date is optional and can fall back on default colours.
            # Colours are stored in a separate dated dictionary as they do not belong in the 2D data frame.
            color_value = date_dict.get('Colour', 'default')
            color_dict[date_value] = color_value

            for k, v in skills_list.items():
                if type(v) not in [int, float, complex]:
                    v = None
                    print('Date: %s  Skill: %s  is non-numeric - point will not be plotted' % (date_value, str(k)))
                un_pivoted.append([date_value, k, v])

        except (KeyError, ValueError):
            # If any data was added before the exception occurred, use date_value to remove this data from un_pivoted.
            # If the error occurred before date_value was set, it will have a None value and no data will be removed.
            un_pivoted[:] = [x for x in un_pivoted if x[0] != date_value]       # list comprehension
            print_success_error('Skipping Item %i of "Skills By Date" - invalid format. (item indeces start at 0)'
                                % index_, is_success=False)

    # Convert the un-pivoted data into a Pandas DataFrame
    df = pd.DataFrame(un_pivoted, columns=['date', 'skill_name', 'skill_value'])
    df.sort_values(['date', 'skill_name'], inplace=True)
    min_skill = int(min(df['skill_value']))
    max_skill = int(max(df['skill_value']))

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

    # Use the number of different skills to set the angles for each 'limb' (xtick) on the radar chart.
    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]        # need to complete the polygon by plotting back to the first point again.
    plt.xticks(angles[:-1], skill_name_list, color='grey', size=8)

    # Add y axis ticks to one of the radar chart limbs.
    ax.set_rlabel_position(0)
    plt.yticks(range(min_skill, max_skill+1), color='grey', size=7)
    plt.ylim(min_skill-1, max_skill+1)

    # Plot one polygon for each date in the DataFrame.
    for index_, (label, content) in enumerate(df.items()):
        # without .tolist(), the 'list' seems to contain more than expected - type ndarray instead of list
        values = content.tolist()
        values += values[:1]        # Need to complete the polygon by plotting back to the first point again.
        
        line_ = ax.plot(angles, values, linewidth=1, linestyle='solid', label=label)
        fill_ = ax.fill(angles, values, alpha=0.3)
        # Handle colours separately as user input may be missing/invalid.
        # Missing values are replaced by 'default' in an earlier section. 'default' also raises a ValueError exception
        try:
            plot_color = mpl_colors.to_rgb(color_dict[label])
            line_[0].set_color(plot_color)
            fill_[0].set_color(plot_color)
        except (KeyError, ValueError):
            print('Config "Colour" key missing/invalid for %s. Using default colour' % label)

    # Set the chart title, if provided.
    try:
        plt.title(parsed['Chart Title'])
    except KeyError:
        print('Config "Chart Title" key missing/invalid. No title will be displayed')

    # Set the chart dimensions, if provided.
    try:
        chart_size = parsed['Chart Size']
        chart_width = chart_size['Width']
        chart_height = chart_size['Height']
        fig.set_size_inches(chart_width, chart_height)
    except (KeyError, ValueError):
        print('Config "Chart Size" key missing/invalid. Default size will be used')

    # Add a legend across the bottom of the chart.
    plt.legend(bbox_to_anchor=(0., -.15, 1., .102), loc=3,
               ncol=3, mode="expand", borderaxespad=0., fontsize=8)

    # Save the plot if a valid path has been provided. Otherwise display the plot.
    # Also display the plot if there is an error on saving.
    display_plot = False
    if save_path is not None:
        try:
            plt.savefig(fname=save_path)
            print_success_error('Figure saved to:  ' + save_path, is_success=True)
        except (FileNotFoundError, ValueError) as exception_:
            print_success_error('Error when saving figure, displaying instead \nError message: \n\n' + str(exception_),
                                is_success=False)
            display_plot = True
    else:
        display_plot = True

    if display_plot:
        print_success_error('Displaying plot', is_success=True)
        plt.show()


def main():
    # Initiates the script by handling the arguments passed from the command line.

    example_yaml = '''
            # Please format the config file in line with the following example - YAML syntax.
            # Colours can be hex codes if enclosed in quotes.
            # Mandatory keys: "Skills By Date", "Date", "Skills".
            
            Chart Title: DEMO Python Skill Progression
            Chart Size  :
              Width   : 4
              Height  : 4
            Skills By Date:
              - Date    : 2019-04-08
                Colour  : blue
                Skills  :
                  Skill 1 : 2
                  Skill 2 : 5
    
              - Date    : 2019-04-12
                Skills  :
                  Skill 1 : 3
                  Skill 2 : 5.3
                  Skill 5 : 4
          '''

    cmd_text = 'script to plot progress in Python skills, input via the config file'
    parser = argparse.ArgumentParser(description=cmd_text)
    parser.add_argument('-c', '--config',
                        help='Input path of config YAML file',
                        action='store')
    parser.add_argument('-s', '--save',
                        help=
                        'Input save path INCLUDING file extension'
                        'If no valid path is provided, chart will be displayed instead',
                        action='store')
    parser.add_argument('-e', '--example',
                        help='Display example of expected config file format',
                        action='store_true')
    parser.add_argument('-d', '--demo',
                        help='Display the output that will result from the example config',
                        action='store_true')
    args = parser.parse_args()

    # Can't make config or example mandatory since having one OR the other is acceptable. Handle here instead.
    if args.config is None and not args.example and not args.demo:
        print('Please supply the path of a config file using -c, or use -h / -e / -d for help / example / demo')

    elif args.example:
        print(example_yaml)

    elif args.demo:
        radar_chart(example_yaml, args.save)

    else:
        # Check that the config file exists, and read content from it.
        if os.path.isfile(args.config):
            with open(args.config, 'r') as f:
                config_yaml = f.read()
        else:
            print_success_error('Invalid config path provided. Chart will not be plotted', is_success=False)
            return

        radar_chart(config_yaml, args.save)

main()