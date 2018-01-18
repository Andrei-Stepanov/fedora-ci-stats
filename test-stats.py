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
import copy
import argparse

DIST_GIT_URL = 'https://src.fedoraproject.org/'
UPSTREAMFIRST_URL = "https://upstreamfirst.fedorainfracloud.org/"
J2_WIKI_TEMPLATE = 'stat.j2'

# Package info schema.
pkg_template = {'name': '',
                'distgit': {
                    'package_url': '',
                    'test_yml': '',
                    'missing': '',
                    'pending': {'status': '', 'url': '', 'user': {}},
                    'test_tags': {'classic': '', 'container': '', 'atomic': ''}},
                'upstreamfirst': {'test_yml': '',
                                  'package_url': '',
                                  'test_tags': {'classic': '', 'container': '', 'atomic': ''}}}
ipkgs = list()

def get_pkgs_stat():
    """Generataes packages statistic.

    Parameters
    ----------
    packages : list
        List of packages.

    Returns
    -------
    dict
        Statistic in json.
    """
    print('Get packages statistic.')
    sys.stdout.flush()
    statistic_json = {'total': '',
                      'distgit': {
                          'test_yml': '',
                          'missing': '',
                          'pending': '',
                          'test_tags': {'classic': '', 'container': '', 'atomic': ''}},
                      'upstreamfirst': {'test_yml': '',
                                        'test_tags': {'classic': '', 'container': '', 'atomic': ''}}}
    total = pkgs_in_cat('distgit', 'test_yml')
    statistic_json['distgit']['test_yml'] = total
    total = pkgs_in_cat('distgit', 'missing')
    statistic_json['distgit']['missing'] = total
    total = pkgs_in_cat('distgit', 'pending', 'status')
    statistic_json['distgit']['pending'] = total
    total = pkgs_in_cat('distgit', 'test_tags', 'classic')
    statistic_json['distgit']['test_tags']['classic'] = total
    total = pkgs_in_cat('distgit', 'test_tags', 'container')
    statistic_json['distgit']['test_tags']['container'] = total
    total = pkgs_in_cat('distgit', 'test_tags', 'atomic')
    statistic_json['distgit']['test_tags']['atomic'] = total
    total = pkgs_in_cat('upstreamfirst', 'test_yml')
    statistic_json['upstreamfirst']['test_yml'] = total
    total = pkgs_in_cat('upstreamfirst', 'test_tags', 'classic')
    statistic_json['upstreamfirst']['test_tags']['classic'] = total
    total = pkgs_in_cat('upstreamfirst', 'test_tags', 'container')
    statistic_json['upstreamfirst']['test_tags']['container'] = total
    total = pkgs_in_cat('upstreamfirst', 'test_tags', 'atomic')
    statistic_json['upstreamfirst']['test_tags']['atomic'] = total
    return statistic_json

def pkgs_in_cat(*args):
    """Returns stats for package.

    Returns
    -------
    str
        Formatted string, for example: '48 (42%)'.
    """
    total_packages = len(ipkgs)
    total = 0
    for pkg in ipkgs:
        if len(args) == 2:
            if pkg[args[0]][args[1]]:
                total += 1
        else:
            if pkg[args[0]][args[1]][args[2]]:
                total += 1
    percent = round((100 * in_category) / total_packages)
    total = "{} ({}%)".format(total, percent)
    return total

def get_pull_requests(base_url, pkg):
    """Get pull requests from site using API.

    Parameters
    ----------
    base_url : str
        Pagure URL.
    pkg : str
        Name of the package.

    Returns
    -------
    Json
        Info about PR
    """
    url = base_url + 'api/0/rpms/' + pkg + '/pull-requests'
    response = requests.get(url)
    try:
        pr = response.json()
    except ValueError:
        print("Can't get {} URL. It will be skipped".format(url))
        return
    return pr

def manage_pull_request(response_json):
    """Checks if PR corresponds to the test PR and open.

    Parameters
    ----------
    response_json : json
        Info about PR.

    Returns
    -------
    json
        {'user': <username>, 'url': <pull_req_url>}
    """
    if response_json['total_requests'] <= 0:
        return
    for request in response_json['requests']:
        try:
            if ('test' in request['title']) and (request['status'] == 'Open'):
                pull_req_url = DIST_GIT_URL + request['project']['url_path'] + '/pull-requests'
                return {'user': request['user'], 'url': pull_req_url}
        except (KeyError, TypeError):
            print('Exception for %s' % request)


def get_projects_url_patches(json_response):
    """Get projects url patches.
    """
    projects_url_patches = []
    for project in json_response['projects']:
        project_name = project['url_path']
        projects_url_patches.append(project_name)
    return projects_url_patches


def get_file_from_site(url, package, test_file='tests.yml'):
    """Get file from the site.

    Parameters
    ----------
    url : str
        Url, for example: 'https://upstreamfirst.fedorainfracloud.org/'
    package : str
        Package name
    test_file : str
        File name to get from site.

    Returns
    -------
        test.yaml (raw string)
    """
    if 'upstreamfirst' in url:
        test_file_url = url + package + '/raw/master/f/' + test_file
    elif 'fedoraproject' in url:
        test_file_url = url + '/rpms/' + package + '/raw/master/f/tests/' + test_file
    else:
        return
    response = requests.get(test_file_url)
    return response.text


def get_url_to_test_yml(url, package):
    """Get url to the test.yml file

    Parameters
    ----------
    url : str
        Url, for example: 'https://upstreamfirst.fedorainfracloud.org/'
    package : str
        Name of the package.

    Returns
    -------
        Url string.
    """
    if 'upstreamfirst' in url:
        test_file_url = url + package + '/blob/master/f/tests.yml'
    elif 'fedoraproject' in url:
        test_file_url = url + 'rpms/' + package + '/blob/master/f/tests/tests.yml'
    else:
        return
    return test_file_url

def check_if_file_exists(url):
    """Checks if file exists.

    Parameters
    ----------
    url : str
        Url to the file.

    Returns
    -------
    bool
        True/False if file exists.
    """
    response = requests.get(test_file_url)
    if response.status_code == 200:
        return True
    else:
        return False

def get_test_tags(raw_text):
    """Just returns existed test-tags.

    Parameters
    ----------
    raw_text : str(string): raw text output from the requests

    Returns:
        tags (list if strings)
    """
    test_tags = []

    for tag in ['classic', 'container', 'atomic']:
        if tag in raw_text:
            test_tags.append(tag)

    return test_tags


def handle_test_tags(url, pkg):
    """Gets new path to the test.yaml if existing test.yaml includes
    test file.

    Parameters
    ----------
    url : str
        Example: 'https://upstreamfirst.fedorainfracloud.org/'
    pkg : str
        Name of the pkg.

    Returns
    -------
    list
        List of strings.
    """
    raw_text = get_file_from_site(url, pkg)
    if 'Page not found' in raw_text:
        return []
    test_tags = get_test_tags(raw_text)
    if not test_tags:
        new_test_file = re.findall(r'(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', raw_text)
        if new_test_file:
            raw_text = get_file_from_site(url, pkg, new_test_file[-1])
            test_tags = get_test_tags(raw_text)
    return test_tags

def test_tags_to_dict(test_tags):
    """Convert test-tags list to the dictionary.
    """
    tags_dict = {'classic': False, 'container': False, 'atomic': False}
    try:
        for tag in test_tags:
            tags_dict[tag] = True
    except TypeError:
        pass
    return tags_dict

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
    """Gather package information.
    """
    raw_text = get_pull_requests(DIST_GIT_URL, pkg)
    pr = manage_pull_request(raw_text)
    info = copy.deepcopy(pkg_template)
    info['name'] = pkg
    if pr:
        try:
            info['distgit']['pending']['url'] = pr['url']
            info['distgit']['pending']['user'] = pr['user']
            info['distgit']['pending']['status'] = True
        except KeyError:
            if pr['error_code'] == 'ENOPROJECT':
                info['distgit']['missing'] = True
    elif pr is None:
        info['distgit']['pending']['url'] = ''
        info['distgit']['pending']['user'] = ''
        info['distgit']['pending']['status'] = False
    # Get upstreamfirst test-tags
    upstream_test_tags = handle_test_tags(UPSTREAMFIRST_URL, pkg)
    upstream_test_tags = test_tags_to_dict(upstream_test_tags)
    info['upstreamfirst']['test_tags'] = upstream_test_tags
    upstream_url_to_test_yml = get_url_to_test_yml(UPSTREAMFIRST_URL, pkg)
    if check_if_file_exists(upstream_url_to_test_yml):
        info['upstreamfirst']['test_yml'] = True
        info['upstreamfirst']['package_url'] = upstream_url_to_test_yml
    else:
        info['upstreamfirst']['test_yml'] = False
        info['upstreamfirst']['package_url'] = ''
    # Get distgit test-tags
    dist_git_test_tags = handle_test_tags(DIST_GIT_URL, pkg)
    dist_git_test_tags = test_tags_to_dict(dist_git_test_tags)
    info['distgit']['test_tags'] = dist_git_test_tags
    dist_git_url_to_test_yml = get_url_to_test_yml(DIST_GIT_URL, pkg)
    if check_if_file_exists(dist_git_url_to_test_yml):
        info['distgit']['test_yml'] = True
        info['distgit']['package_url'] = dist_git_url_to_test_yml
    else:
        info['distgit']['test_yml'] = False
        info['distgit']['package_url'] = ''
    # Write results to the file
    print('Gathering info for {}'.format(info['name']))
    sys.stdout.flush()
    ipkgs.append(info)

def get_all_projects(url):
    """Get all projects from site using API.

    Parameters
    ----------
    url (string): url of the site
        For example: 'https://upstreamfirst.fedorainfracloud.org/'

    Returns
    -------
    json
        Response for all projects.
    """
    site = url + 'api/0/projects'
    response = requests.get(site)
    return response.json()

def get_projects_names(json_response):
    """Get projects names from the all projects

    Parameters
    ----------
    json_response : json
        All projects.

    Returns
    -------
    list
        List of strings names of projects.
    """
    projects_names = []
    for project in json_response['projects']:
        project_name = project['fullname']
        if 'forks/' not in project_name:
            projects_names.append(project_name)
    return projects_names

def get_pkgs_file(fname):
    """Reads list of packages from a fname

    Parameters
    ----------
    fname : file
        File to get packages from. One per line.

    Returns
    -------
    list
        List of packages.
    """
    with open(fname) as fin:
        pkgs = fin.read().splitlines()
    for element in pkgs if element.startswith('#'):
        pkgs.remove(element)
    return pkgs

def get_pkgs_url(url):
    projects = get_all_projects(url)
    pkgs = get_projects_names(projects)
    return pkgs


def get_list_of_dicts(dict_of_strings):
    pkgs = []
    for pkg in dict_of_strings:
        pkgs.append(eval(pkg))
    return pkgs

def generate_file_upload_on_wiki(fin, fout):
    """Generate wiki page file.

    Parameters
    ----------
        fin : file
            File with packages.
        fout : file
            File with packages in json format.

    Returns
    -------
    file
        File to be uploaded to wiki.
    """
    print('Convert to wiki format: %s -> %s.' % ())
    pkgs = get_pkgs_file(fin)
    pkgs_stat = get_pkgs_stat(pkgs)
    pkgs = get_list_of_dicts(pkgs)
    cdir = os.path.dirname(os.path.abspath(__file__))
    j2_loader = jinja2.FileSystemLoader(cdir)
    j2_env = jinja2.Environment(loader=j2_loader, trim_blocks=True)
    template = j2_env.get_template(J2_WIKI_TEMPLATE)
    template_vars = {'updated': datetime.datetime.utcnow(),
                     'total': pkgs_stat, 'pkgs': pkgs}
    with open(fout, 'w') as mwfile:
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
        generate_file_upload_on_wiki(fin=FILE_PACKAGES, fout=opts.wikiout)

if __name__ == '__main__':
    main()
