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

# http://sphinxcontrib-napoleon.readthedocs.io/en/latest/index.html

import sys
import argparse

UPSTREAMFIRST_URL = 'https://upstreamfirst.fedorainfracloud.org/'
DIST_GIT_URL = 'https://src.fedoraproject.org/'
FILE_PACKAGES = 'upstreamfirst_packages.txt'
DEFAULT_URL = 'fedoraproject.org'
UPSTREAM_PAGURE = "https://upstreamfirst.fedorainfracloud.org/api/0/"
UPSTREAM_BASE = "https://upstreamfirst.fedorainfracloud.org/"
DISTGIT_BASE = "https://src.fedoraproject.org/git/rpms/"
IN_J2_WIKI_TEMPLATE = 'stat.j2'

# Pagure information about package.
package_json = {'name': '',
                'distgit': {
                    'package_url': '',
                    'test_yml': '',
                    'missing': '',
                    'pending': {'status': '', 'url': '', 'user': {}},
                    'test_tags': {'classic': '', 'container': '', 'atomic': ''}},
                'upstreamfirst': {'test_yml': '',
                                  'package_url': '',
                                  'test_tags': {'classic': '', 'container': '', 'atomic': ''}}}


def get_packages_statistic(packages):
    """Function gets packages statistic

    Args:
        packages (list): list of packages

    Returns:
        statistic_json (dict): packages statistic
    """
    print('Get packages statistic')
    sys.stdout.flush()
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


def get_pull_requests(site_url, package):
    """Get pull requests from site using API

    Parameters
    ----------
        site_url : str
            url of the site for example: 'https://upstreamfirst.fedorainfracloud.org/'
        package : str
            Name of the package.

    Returns
    -------
    Json
        Info about PR
    """
    site = site_url + 'api/0/rpms/' + package + '/pull-requests'

    response = requests.get(site)
    try:
        pull_request = response.json()
        return pull_request
    except ValueError:
        print("Can't get {} URL. It will be skipped".format(site))
        return


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
                if ('Add CI tests' in request['title']) and (request['status'] == 'Open'):
                    pull_req_url = DIST_GIT_URL + request['project']['url_path'] + '/pull-requests'
                    return {'user': request['user'], 'url': pull_req_url}

    except (KeyError, TypeError):
        print('Exception:', response_json)






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

    except TypeError:
        pass
    return tags_dict


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


def get_pkgs_info(repos, short=False):
    # Create file with info about packages.
    if 'https://' in repos:
        pkgs = get_pkgs_url(repos)
    else:
        pkgs = get_pkgs_file(repos)
    if short:
        pkgs = pkgs[:10]
    for pkg in pkgs:
        get_pkg_info(pkg)

def get_pkg_info(pkg):
    """Updates package_json with correct information.
    """
    raw_text = get_pull_requests(DIST_GIT_URL, pkg)
    result = manage_pull_request(raw_text)
    package_json['name'] = pkg
    if result is not None:
        try:
            package_json['distgit']['pending']['url'] = result['url']
            package_json['distgit']['pending']['user'] = result['user']
            package_json['distgit']['pending']['status'] = True
        except KeyError:
            if result['error_code'] == 'ENOPROJECT':
                package_json['distgit']['missing'] = True
    elif result is None:
        package_json['distgit']['pending']['url'] = ''
        package_json['distgit']['pending']['user'] = ''
        package_json['distgit']['pending']['status'] = False
    # Get upstreamfirst test-tags
    upstream_test_tags = handle_test_tags(UPSTREAMFIRST_URL, pkg)
    upstream_test_tags = test_tags_to_dict(upstream_test_tags)
    package_json['upstreamfirst']['test_tags'] = upstream_test_tags
    upstream_url_to_test_yml = get_url_to_test_yml(UPSTREAMFIRST_URL, pkg)
    if check_if_test_yml_exists(upstream_url_to_test_yml):
        package_json['upstreamfirst']['test_yml'] = True
        package_json['upstreamfirst']['package_url'] = upstream_url_to_test_yml
    else:
        package_json['upstreamfirst']['test_yml'] = False
        package_json['upstreamfirst']['package_url'] = ''
    # Get distgit test-tags
    dist_git_test_tags = handle_test_tags(DIST_GIT_URL, pkg)
    dist_git_test_tags = test_tags_to_dict(dist_git_test_tags)
    package_json['distgit']['test_tags'] = dist_git_test_tags
    dist_git_url_to_test_yml = get_url_to_test_yml(DIST_GIT_URL, pkg)
    if check_if_test_yml_exists(dist_git_url_to_test_yml):
        package_json['distgit']['test_yml'] = True
        package_json['distgit']['package_url'] = dist_git_url_to_test_yml
    else:
        package_json['distgit']['test_yml'] = False
        package_json['distgit']['package_url'] = ''
    # Write results to the file
    print('Gathering info for {}'.format(package_json['name']))
    sys.stdout.flush()
    write_results_to_the_file(package_json, FILE_PACKAGES)

def get_all_projects(site_url):
    """Get all projects from site using API.

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

def get_pkgs_file(file):
    """Reads list of packages from a file

    Args:
        file (file): file to get packages from

    Returns:
        packages (list of packages)
    """
    with open(file) as packages_file:
        packages = packages_file.read().splitlines()
        [packages.remove(element) for element in packages if element.startswith('#')]
        return packages

def get_pkgs_url(url):
    projects = get_all_projects(url)
    pkgs = get_projects_names(projects)
    return pkgs


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
    sys.stdout.flush()
    packages = get_pkgs_file(input_file)
    packages_statistic = get_packages_statistic(packages)
    packages = get_list_of_dicts(packages)
    this_dir = os.path.dirname(os.path.abspath(__file__))
    j2_loader = jinja2.FileSystemLoader(this_dir)
    j2_env = jinja2.Environment(loader=j2_loader, trim_blocks=True)
    template = j2_env.get_template(IN_J2_WIKI_TEMPLATE)
    template_vars = {'updated': datetime.datetime.utcnow(),
                     'total': packages_statistic, 'pkgs': packages}
    with open(output_file, 'w') as mwfile:
        for line in template.render(template_vars):
            mwfile.write(line)

def main():
    parser = argparse.ArgumentParser(
        description='Gather stats about tests in dist-git')
    parser.add_argument("--wikiout", metavar='FILE', default=None,
                        help="Dump output to FILE in MediaWiki format.")
    parser.add_argument("--reposlist", metavar='REPOSFILE', default=None,
                        required=True,
                        help=("File or URL with repos. Could be whether "
                              "https://upstreamfirst.fedorainfracloud.org/ or "
                              "https://src.fedoraproject.org/'."))
    parser.add_argument("--short", help="Proceed only first 10 repos.",
                        action='store_true')
    opts = parser.parse_args()
    get_pkgs_info(opts.reposlist, short=opts.short)
    if opts.wikiout:
        generate_file_upload_on_wiki(input_file=FILE_PACKAGES, output_file=opts.wikiout)

if __name__ == '__main__':
    main()
