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

import argparse

from config import UPSTREAMFIRST_URL
from config import DIST_GIT_URL
from config import FILE_PACKAGES

from tools import check_if_test_yml_exists
from tools import delete_files_before_running
from tools import get_all_projects
from tools import get_list_of_packages_from_the_file
from tools import get_projects_names
from tools import get_pull_requests
from tools import get_url_to_test_yml
from tools import handle_test_tags
from tools import manage_pull_request
from tools import test_tags_to_dict
from tools import write_results_to_the_file

from generate_file_upload_wiki import generate_file_upload_on_wiki


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


def wrapper_for_get_pull_requests(package):
    """Function updates package_json with correct information"""

    raw_text = get_pull_requests(DIST_GIT_URL, package)
    result = manage_pull_request(raw_text)
    package_json['name'] = package

    if result is not None:
        package_json['distgit']['pending']['url'] = result['url']
        package_json['distgit']['pending']['user'] = result['user']
        package_json['distgit']['pending']['status'] = True
    else:
        package_json['distgit']['pending']['url'] = ''
        package_json['distgit']['pending']['user'] = ''
        package_json['distgit']['pending']['status'] = False

    # Get upstreamfirst test-tags
    upstream_test_tags = handle_test_tags(UPSTREAMFIRST_URL, package)
    upstream_test_tags = test_tags_to_dict(upstream_test_tags)
    package_json['upstreamfirst']['test_tags'] = upstream_test_tags

    upstream_url_to_test_yml = get_url_to_test_yml(UPSTREAMFIRST_URL, package)
    if check_if_test_yml_exists(upstream_url_to_test_yml):
        package_json['upstreamfirst']['test_yml'] = True
        package_json['upstreamfirst']['package_url'] = upstream_url_to_test_yml
    else:
        package_json['upstreamfirst']['test_yml'] = False
        package_json['upstreamfirst']['package_url'] = ''

    # Get distgit test-tags
    dist_git_test_tags = handle_test_tags(DIST_GIT_URL, package)
    dist_git_test_tags = test_tags_to_dict(dist_git_test_tags)
    package_json['distgit']['test_tags'] = dist_git_test_tags

    dist_git_url_to_test_yml = get_url_to_test_yml(DIST_GIT_URL, package)
    if check_if_test_yml_exists(dist_git_url_to_test_yml):
        package_json['distgit']['test_yml'] = True
        package_json['distgit']['package_url'] = dist_git_url_to_test_yml
    else:
        package_json['distgit']['test_yml'] = False
        package_json['distgit']['package_url'] = ''

    # Write results to the file
    print('Gathering info for {}'.format(package_json['name']))
    write_results_to_the_file(package_json, FILE_PACKAGES)


def get_projects_list_from_url(site_url):
    # Get all open pull requests
    projects = get_all_projects(UPSTREAMFIRST_URL)
    all_packages = get_projects_names(projects)
    return all_packages


def create_file_with_packages_data(input_data, short=False):
    # Create file with packages_data input data is a file or an URL. Filename is config.FILE_PACKAGES
    if 'https://' in input_data:
        all_packages = get_projects_list_from_url(input_data)
    else:
        all_packages = get_list_of_packages_from_the_file(input_data)

    if short:
        all_packages = all_packages[:10]

    for package in all_packages:
        wrapper_for_get_pull_requests(package)
    return


def main():
    parser = argparse.ArgumentParser(description='Gather stats about tests in dist-git')
    parser.add_argument("--wikiout", metavar='FILE', default=None, help="Dump output to FILE in MediaWiki format.")
    parser.add_argument("--reposlist",
                        metavar='REPOSFILE',
                        default=None,
                        help="File or URL with repos. Could be whether 'https://upstreamfirst.fedorainfracloud.org/' "
                             "or 'https://src.fedoraproject.org/'. One repo per line.",
                        required=True)
    parser.add_argument("--short", help="Proceed only first 10 repos.")
    opts = parser.parse_args()

    # Prepare environment
    print('Prepare environment')
    delete_files_before_running([FILE_PACKAGES, opts.wikiout])

    if opts.wikiout and opts.short:
        create_file_with_packages_data(opts.reposlist, short=True)
        generate_file_upload_on_wiki(input_file=FILE_PACKAGES, output_file=opts.wikiout)
    elif opts.wikiout:
        create_file_with_packages_data(opts.reposlist)
        generate_file_upload_on_wiki(input_file=FILE_PACKAGES, output_file=opts.wikiout)
    elif opts.short:
        create_file_with_packages_data(opts.reposlist, short=True)
    else:
        create_file_with_packages_data(opts.reposlist)


if __name__ == '__main__':
    main()
