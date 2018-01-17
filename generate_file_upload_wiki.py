#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright Red Hat Inc
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# This file is part of Cockpit.

import datetime
import jinja2
import os

from config import IN_J2_WIKI_TEMPLATE

from tools import get_list_of_packages_from_the_file


def get_list_of_dicts(dict_of_strings):
    result = []
    for package in dict_of_strings:
        result.append(eval(package))
    return result


def generate_file_upload_on_wiki(input_file, output_file):
    """Generate file that will be uploaded on the wiki page

    Args:
        input_file (file): file with packages
        output_file (file): file with packages in json format

    Returns:
        (file): file that will be uploaded on the wiki page
    """
    print('Generate file that will be uploaded on the wiki page')
    THIS_DIR = os.path.dirname(os.path.abspath(__file__))
    packages = get_list_of_packages_from_the_file(input_file)
    packages_statistic = get_packages_statistic(packages)
    packages = get_list_of_dicts(packages)

    j2_loader = jinja2.FileSystemLoader(THIS_DIR)
    j2_env = jinja2.Environment(loader=j2_loader, trim_blocks=True)
    template = j2_env.get_template(IN_J2_WIKI_TEMPLATE)

    template_vars = {'updated': datetime.datetime.utcnow(), 'total': packages_statistic, 'pkgs': packages}

    with open(output_file, 'w') as mwfile:
        for line in template.render(template_vars):
            mwfile.write(line)


def get_packages_statistic(packages):
    """Function gets packages statistic

    Args:
        packages (list): list of packages

    Returns:
        statistic_json (dict): packages statistic
    """
    print('Get packages statistic')
    statistic_json = {'total': '',
                      'distgit': {
                          'test_yml': '',
                          'missing': '',
                          'pending': '',
                          'test_tags': {'classic': '', 'container': '', 'atomic': ''}},
                      'upstreamfirst': {'test_yml': '',
                                        'test_tags': {'classic': '', 'container': '', 'atomic': ''}}}
    total_packages = len(packages)
    statistic_json['total'] = str(total_packages)
    statistic_json['distgit']['test_yml'] = _get_packages_number_in_category(total_packages, packages,
                                                                             'distgit', 'test_yml')
    statistic_json['distgit']['missing'] = _get_packages_number_in_category(total_packages, packages,
                                                                            'distgit', 'missing')
    statistic_json['distgit']['pending'] = _get_packages_number_in_category(total_packages, packages,
                                                                            'distgit', 'pending', 'status')
    statistic_json['distgit']['test_tags']['classic'] = _get_packages_number_in_category(total_packages, packages,
                                                                                         'distgit',
                                                                                         'test_tags', 'classic')
    statistic_json['distgit']['test_tags']['container'] = _get_packages_number_in_category(total_packages, packages,
                                                                                           'distgit',
                                                                                           'test_tags', 'container')
    statistic_json['distgit']['test_tags']['atomic'] = _get_packages_number_in_category(total_packages, packages,
                                                                                        'distgit',
                                                                                        'test_tags', 'atomic')

    statistic_json['upstreamfirst']['test_yml'] = _get_packages_number_in_category(total_packages, packages,
                                                                                   'upstreamfirst', 'test_yml')
    statistic_json['upstreamfirst']['test_tags']['classic'] = _get_packages_number_in_category(total_packages, packages,
                                                                                               'upstreamfirst',
                                                                                               'test_tags', 'classic')
    statistic_json['upstreamfirst']['test_tags']['container'] = _get_packages_number_in_category(total_packages,
                                                                                                 packages,
                                                                                                 'upstreamfirst',
                                                                                                 'test_tags',
                                                                                                 'container')
    statistic_json['upstreamfirst']['test_tags']['atomic'] = _get_packages_number_in_category(total_packages, packages,
                                                                                              'upstreamfirst',
                                                                                              'test_tags', 'atomic')
    return statistic_json


def _get_packages_number_in_category(total_packages, all_packages, *args):
    """
    Function returns updated statistic_json from the get_packages_statistic()
    Args:
        total_packages (int): total packages
        all_packages (list of jsons): all packages

    Returns:
        formatted_string (all_packages):
            for example: '48 (42%)'
    """
    number_in_category = 0
    for item in all_packages:
        dict_pack = eval(item)

        if len(args) == 2:
            if dict_pack[args[0]][args[1]]:
                number_in_category += 1
        else:
            if dict_pack[args[0]][args[1]][args[2]]:
                number_in_category += 1
    formatted_string = "{} ({}%)".format(number_in_category, round((100 * number_in_category) / total_packages))
    return formatted_string


if __name__ == '__main__':
    exit(0)
