#!/usr/bin/python3

import os
import shutil
import subprocess
import glob
import logging
import urllib.request
import tarfile
import yaml
import argparse


class ArchDB():
    def __enter__(self):
        return self.open_db()
    def __init__(self, source, repo):
        self.source = source
        self.repo = repo

        self.db_url = self.source + '/' + self.repo + '.db'
        self.dbfile = '/tmp/' + repo + '.db'       
    def __exit__(self, type, value, traceback):
        logging.info("Removing temporary database " + self.dbfile)
        os.remove(self.dbfile)
    
    def open_db(self):
        logging.info("Getting database " + self.db_url + "...")
        urllib.request.urlretrieve(self.db_url, self.dbfile)
        return tarfile.open(self.dbfile, mode = 'r:gz')
    
    
def download_files(source, filenames, dest):
    local_fnames = []
    for fname in filenames:
        print('Downloading ' + source + '/' + fname + '...')
        (local_fname, _) = urllib.request.urlretrieve(
            source + '/' + fname, filename = dest + '/' + fname)
        local_fnames.append(local_fname)
    return local_fnames
    
def get_file_list(packages, db):
    dirs = filter(lambda x: x.find('/') == -1, db.getnames())

    def selecter(dirname):
        for pkgname in packages:
            if dirname.find(pkgname) == 0:
                return True
        return False

    def get_pkg_filename(dirname):
        with db.extractfile(dirname + '/desc') as descfile:
            #Read line after %FILENAME%
            while(descfile.readline().decode('utf-8') is '%FILENAME%\n' < 0):
                pass
            return descfile.readline().decode('utf-8').rstrip()
        
    return list(map(get_pkg_filename, filter(selecter, dirs)))


def main(*args):
    parser = argparse.ArgumentParser(description=
        '''Set up archlinux repository containing listed packages.''')
    parser.add_argument('config', metavar='CONFIG', help='config file')

    args = parser.parse_args(args)
    print("Using configuration from", args.config)
    with open(args.config, 'r') as config_fh:
        config = yaml.load(config_fh)

    source = config['source']
    dest = config['dest']
    repo = config['repo']
    selected_packages = config['packages']

    shutil.rmtree(dest)
    os.mkdir(dest)

    logging.info("Opening database")
    
    with ArchDB(source, repo) as db:
        file_list = get_file_list(selected_packages, db)

    sig_file_list = list(map(lambda name: name + '.sig', file_list))

    local_files = download_files(source, file_list, dest)
    download_files(source, sig_file_list, dest)
    print("Invoking repo-add")
    logging.info("Invoking " +
                 ' '.join(["repo-add", "-v",
                           dest + '/' + repo + '.db.tar.gz'] + local_files))
    subprocess.call(["repo-add", "-v",
                     dest + '/' + repo + '.db.tar.gz'] + local_files)
 
if __name__ == '__main__':
    main()










