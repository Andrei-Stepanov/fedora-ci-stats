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

import os
import re
import requests

from config import DIST_GIT_URL


def get_pull_requests(site_url, package):
    """Get pull requests from site using API

    Args:
        site_url (string): url of the site
            for example: 'https://upstreamfirst.fedorainfracloud.org/'
        package (string): name of the package

    Returns:
        response (json): info about PR
    """
    site = site_url + 'api/0/rpms/' + package + '/pull-requests'

    response = requests.get(site)
    return response.json()


def manage_pull_request(response_json):
    """Checks if PR corresponds to the test PR and open.

    Args:
        response_json (json): info about PR

    Returns:
         (json): {'user': <username>, 'url': <pull_req_url>}
    """
    try:
        if response_json['total_requests'] > 0:
            for request in response_json['requests']:
                if ('Add CI tests' or 'test' in request['title']) and (request['status'] == 'Open'):
                    pull_req_url = DIST_GIT_URL + request['project']['url_path'] + '/pull-requests'
                    return {'user': request['user'], 'url': pull_req_url}

    except Exception:
        # {'error': 'Project not found', 'error_code': 'ENOPROJECT'}
        return


def get_all_projects(site_url):
    """Get all projects from site using API

    Args:
        site_url (string): url of the site
            for example: 'https://upstreamfirst.fedorainfracloud.org/'

    Returns:
        response (json): all projects
    """
    site = site_url + 'api/0/projects'

    response = requests.get(site)
    return response.json()


def get_projects_names(json_response):
    """Get projects names from the all projects

    Args:
        json_response (json): all projects

    Returns:
        projects_names (list of strings) names of projects
    """

    projects_names = []

    for project in json_response['projects']:
        project_name = project['fullname']
        if 'forks/' not in project_name:
            projects_names.append(project_name)

    return projects_names


def get_projects_url_patches(json_response):
    """Get projects url patches"""

    projects_url_patches = []

    for project in json_response['projects']:
        project_name = project['url_path']

        projects_url_patches.append(project_name)

    return projects_url_patches


def get_test_yaml_from_site(site_url, package, test_file='tests.yml'):
    """Get test.yaml from the site

    Args:
        site_url (string): url of the site
            for example: 'https://upstreamfirst.fedorainfracloud.org/'
        package (string): name of the package
        test_file (string): file to get from site.

    Returns:
        test.yaml (raw string)
    """

    if 'upstreamfirst' in site_url:
        test_file_url = site_url + package + '/raw/master/f/' + test_file
    elif 'fedoraproject' in site_url:
        test_file_url = site_url + '/rpms/' + package + '/raw/master/f/tests/' + test_file
    else:
        return

    response = requests.get(test_file_url)
    return response.text


def get_url_to_test_yml(site_url, package):
    """Get url to the test.yml file

    Args:
        site_url (string): url of the site
            for example: 'https://upstreamfirst.fedorainfracloud.org/'
        package (string): name of the package

    Returns:
        url (string)
    """
    if 'upstreamfirst' in site_url:
        test_file_url = site_url + package + '/blob/master/f/tests.yml'
    elif 'fedoraproject' in site_url:
        test_file_url = site_url + 'rpms/' + package + '/blob/master/f/tests/tests.yml'
    else:
        return

    return test_file_url


def check_if_test_yml_exists(test_file_url):
    """Checks if tesy.yml exists

    Args:
        test_file_url (string): url of the site

    Returns:
        True/False (bool) if response.status_code
    """
    response = requests.get(test_file_url)
    if response.status_code == 200:
        return True
    else:
        return False


def get_test_tags(raw_text):
    """Just returns existed test-tags

    Args:
        raw_text (string): raw text output from the requests

    Returns:
        tags (list if strings)
    """
    test_tags = []

    for tag in ['classic', 'container', 'atomic']:
        if tag in raw_text:
            test_tags.append(tag)

    return test_tags


def handle_test_tags(site_url, package):
    """Function grts new patch to the test.yaml if existing test.yaml includes test file

    Args:
        site_url (string): url of the site
            for example: 'https://upstreamfirst.fedorainfracloud.org/'
        package (string): name of the package

    Returns:
        tags (list of strings)
    """

    raw_text = get_test_yaml_from_site(site_url, package)

    if 'Page not found' in raw_text:
        return []

    test_tags = get_test_tags(raw_text)

    if not test_tags:
        new_test_file = re.findall(r'(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', raw_text)

        if new_test_file:
            raw_text = get_test_yaml_from_site(site_url, package, new_test_file[-1])
            test_tags = get_test_tags(raw_text)

    return test_tags


def test_tags_to_dict(test_tags):
    """Convert test-tags list to the dictionary"""

    tags_dict = {'classic': False, 'container': False, 'atomic': False}
    try:
        for tag in test_tags:
            tags_dict[tag] = True

    except Exception:
        pass
    return tags_dict


def get_list_of_packages_from_the_file(file):
    """Reads list of packages from a file

    Args:
        file (file): file to get packages from

    Returns:
        packages (list of packages)
    """
    with open(file) as packages_file:
        return packages_file.read().splitlines()


def write_results_to_the_file(result, filename):
    """Write results to the file

    Args:
        result (json): package's info
        filename (string): name of the file to write packages

    Returns:
        packages (list of packages)
    """
    with open(filename, 'a') as my_file:
        my_file.write('{}\n'.format(result))

    my_file.close()
    return filename


def delete_files_before_running(files_to_delete):
    """Function deletes (cleanup) files with data

    Args:
        files_to_delete (list): list of files to delete

    Returns:
        (None) if everything is alright
    """
    for file_name in files_to_delete:
        try:
            os.remove(file_name)
        except OSError:
            pass


if __name__ == '__main__':
    exit(0)
