import yaml
import urllib2
import logging
import rospkg
import rospkg.distro
#from django.db import models

logger = logging.getLogger('submit_jobs')

#TODO: Switch to a parsing library for the distro files once it comes out

class DryRosDistro(object):
    def __init__(self, distro):
        self.distro = distro
        self.distro_obj = rospkg.distro.load_distro(rospkg.distro.distro_uri(distro))

    def get_info(self):
        res = {}
        for name, s in self.distro_obj.stacks.iteritems():
            if s.vcs_config.type == 'svn':
                url = s.vcs_config.anon_dev
            else:
                url = s.vcs_config.repo_uri
            res[name] = {'distro': [self.distro + "_dry"],
                         'version': ['latest'],
                         'url': [url],
                         'branch': ['branch']}
        return res



#We're essentially using GitHub as a backend since the distro files are hosted there
class WetRosDistro(object):
    def __init__(self, distro):
        self.distro = distro
        url = 'https://raw.github.com/ros/rosdistro/master/releases/%s.yaml' % distro
        devel_url = 'https://raw.github.com/ros/rosdistro/master/releases/%s-devel.yaml' % distro

        try:
            self.distro_file = yaml.load(urllib2.urlopen(url))
            self.devel_file = yaml.load(urllib2.urlopen(devel_url))
        except:
            logger.error("Could not load rosdistro file or devel file")
            self.distro_file = None
            self.devel_file = None


    def get_info(self):
        res = {}
        for name, r in self.devel_file['repositories'].iteritems():
            if not 'version' in r or not r['version']:
                branch = ""
            else:
                branch = r['version']
            res[name] = {'distro': [self.distro + "_wet"],
                         'version': ['devel'],
                         'url': [r['url']],
                         'branch': [branch]}
        print res
        return res



    def get_repos(self):
        if self.distro_file is None or self.devel_file is None:
            return []
        return list(set(self.distro_file['repositories'].keys() + self.devel_file['repositories'].keys()))

    def is_released(self, repo_name):
        if self.distro_file is None:
            return False
        return self.distro_file['repositories'].has_key(repo_name)

    def get_release_info(self, repo_name):
        if self.distro_file is None:
            return None
        return self.distro_file['repositories'].get(repo_name, None)

    def is_devel(self, repo_name):
        if self.devel_file is None:
            return False
        return self.devel_file['repositories'].has_key(repo_name)

    def get_devel_info(self, repo_name):
        if self.devel_file is None:
            return None
        return self.devel_file['repositories'].get(repo_name, None)

    def get_repo_version(self, repo_name):
        if repo_name not in self.distro_file['repositories']:
            logger.error("Repo %s not in distro file for %s" % (repo_name, self.distro))
            return None

        #Since debian information is tacked onto the version #, we split
        return self.distro_file['repositories'][repo_name]['version'].split('-')[0]
