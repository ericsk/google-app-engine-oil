#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import with_statement

import os
import sys
import zipfile
from getopt import getopt
from shutil import copyfile


def copytree(src, dest, **kw):
    EXCLUDE = ['.svn']
    if os.path.exists(dest):
        if not kw.get('overwrite', False):
            return False
    else:
        os.mkdir(dest, 0755)

    for name in os.listdir(src):
        if name.lower() in EXCLUDE:
            continue
        src_name = os.path.join(src, name)
        dest_name = os.path.join(dest, name)
        if os.path.isdir(src_name):
            copytree(src_name, dest_name)
        else:
            copyfile(src_name, dest_name)


def usage(app_name):
    return 'Usage: %s <project name>' % app_name


def recursively_rmdir(dirname):
    files = os.listdir(dirname)
    for f in files:
        path = os.path.join(dirname, f)
        if os.path.isdir(path):
            recursively_rmdir(path)
        else:
            os.unlink(path)
    os.rmdir(dirname)


def create_file(file_name, content):
    if not os.path.exists(os.path.dirname(file_name)):
        os.makedirs(os.path.dirname(file_name), 0755)
    with open(file_name, 'w') as f:
        f.write('\n'.join(content))


def create_app_yaml(app_yaml_file, project_name):
    create_file(app_yaml_file, [
        'application: %s' % project_name,
        'version: 1',
        'runtime: python',
        'api_version: 1',
        '',
        'derived_file_type:',
        '- python_precompiled',
        '',
        'handlers:',
        '- url: /remote_api',
        '  script: $PYTHON_LIB/google/appengine/ext/remote_api/handler.py',
        '  login: admin',
        '- url: /(img|css|js)/(.*)',
        '  static_files: assets/\\1/\\2',
        '  upload: assets/(img|css|js)/(.*)',
        '- url: /(.*\.(ico|html|txt))',
        '  static_files: static/\\1',
        '  upload: static/(.*\.(ico|html|txt))',
        '- url: /.*',
        '  script: main.py',
        '',
        ])


def create_controller_base(path):
    create_file(path, [
        '',
        'class Bootstrap:',
        '    """',
        '    The base controller init mixin',
        '    """',
        '    def bootstrap(self):',
        '        """',
        '        default initialization method invoked by dispatcher',
        '        """',
        '        pass',
        ])


def create_controller_py(controller_py):
    create_file(controller_py, [
        'from gaeo.controller import Controller',
        '',
        'class Welcome(Controller):',
        '    """The default Controller',
        '',
        '    You could change the default route in main.py',
        '    """',
        '    def index(self):',
        '        """The default method',
        '',
        '        related to templates/welcome/index.html',
        '        """',
        '        pass',
        '',
        ])


def create_base_template(index_html_file):
    create_file(index_html_file, [
        '<!DOCTYPE html>',
        '<html>',
        '    <head>',
        '        <meta charset="UTF-8">',
        '        <title>{% block title %}{% endblock %}</title>',
        '    </head>',
        '    <body>',
        '        {% block content %}{% endblock %}',
        '    </body>',
        '</html>',
        '',
        ])


def create_default_template(index_html_file):
    create_file(index_html_file, [
        '{% extends "../layouts/layout.html" %}',
        '{% block content %}',
        '        <h1>It works!!</h1>',
        '        You could open <i>application/templates/welcome/index.html</i> to edit this page.'
            ,
        '        <!-- this page is related to controller/welcome.py -->'
            ,
        '{% endblock %}',
        '',
        ])


def create_eclipse_project(project_home, project_name):
    proj = os.path.join(project_home, '.project')
    pydevproj = os.path.join(project_home, '.pydevproject')

    create_file(proj, [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<projectDescription>',
        '    <name>%s</name>' % project_name,
        '    <comment></comment>',
        '    <projects>',
        '    </projects>',
        '    <buildSpec>',
        '        <buildCommand>',
        '            <name>org.python.pydev.PyDevBuilder</name>',
        '            <arguments>',
        '            </arguments>',
        '        </buildCommand>',
        '    </buildSpec>',
        '    <natures>',
        '        <nature>org.python.pydev.pythonNature</nature>',
        '    </natures>',
        '</projectDescription>',
        ])

    create_file(pydevproj, [
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
        '<?eclipse-pydev version="1.0"?>',
        '',
        '<pydev_project>',
        '    <pydev_property name="org.python.pydev.PYTHON_PROJECT_VERSION">python 2.5</pydev_property>'
            ,
        '    <pydev_pathproperty name="org.python.pydev.PROJECT_SOURCE_PATH">'
            ,
        '        <path>/%s</path>' % project_name,
        '    </pydev_pathproperty>',
        '</pydev_project>',
        ])


def main(argv):
    ignore_exist_proj = False
    create_eclipse_proj = False
    zipped_core = False

    cur_dir = os.getcwd()

    (optlist, args) = getopt(argv, '', ['eclipse', 'zipped'])

    for (opt, value) in optlist:
        if opt == '--eclipse':
            create_eclipse_proj = True
        elif opt == '--zipped':
            zipped_core = True

    project_name = args[0]

    # create project directory

    project_home = os.path.join(cur_dir, project_name)
    if os.path.exists(project_home):
        print '%s exists' % project_home
        return
    else:
        os.mkdir(project_home, 0755)

    project_name = os.path.basename(project_name).lower()
    template_base = 'oildrum'

    # create <project_name>/application/__init__.py

    application_dir = os.path.join(project_home, 'application')
    create_file(os.path.join(application_dir, '__init__.py'), [])

    controller_dir = os.path.join(application_dir, 'controllers')
    create_file(os.path.join(controller_dir, '__init__.py'), [])

    # create <project_name>/application/controller/application.py

    create_controller_base(os.path.join(controller_dir, 'bootstrap.py'
                           ))

    # create <project_name>/application/controller/welcome.py

    create_controller_py(os.path.join(controller_dir, 'welcome.py'))

    # create base template

    create_base_template(os.path.join(application_dir, 'templates',
                         'layouts', 'layout.html'))

    # create default template

    create_default_template(os.path.join(application_dir, 'templates',
                            'welcome', 'index.html'))

    # create blank model module
    create_file(os.path.join(application_dir, 'models.py'), [
        '#!/usr/bin/env python'])

    # create app.yaml

    create_app_yaml(os.path.join(project_home, 'app.yaml'),
                    project_name)

    target_path = os.path.dirname(os.path.dirname(__file__))
    
    # copy static directories
    static_folder = os.path.join(project_home, 'static')
    copytree(os.path.join(target_path,
             template_base, 'static'), static_folder)
    
    # create assets directories
    assets = ['css', 'js', 'img']
    assets_folder = os.path.join(project_home, 'assets')
    os.mkdir(assets_folder)
    for subdir in assets:
        os.mkdir(os.path.join(assets_folder, subdir))

    # copy lib directory

    lib_folder = os.path.join(project_home, 'lib')
    copytree(os.path.join(target_path,
             template_base, 'lib'), lib_folder)

    # copy plugins directory
    plugin_folder = os.path.join(project_home, 'plugins')
    copytree(os.path.join(target_path, 
        template_base, 'plugins'), plugin_folder)

    # if zipped option is enabled

    if zipped_core:
        os.chdir(project_home)
        z = zipfile.ZipFile(os.path.join('lib','gaeo.zip'), 'w', zipfile.ZIP_DEFLATED)
        dir_list = []
        for (root, dirs, files) in os.walk(os.path.join('lib','gaeo')):
            dir_list.extend([d for d in dirs
                            if os.listdir(os.path.join(root, d)) == []])
            for filename in files:
                z.write(os.path.join(root, filename))
        for d in dir_list:
            z_info = zipfile.ZipInfo(os.path.join(root, d))
            z.writestr(z_info, '')
        z.close()
        recursively_rmdir(os.path.join('lib','gaeo'))
        os.chdir(os.path.join(project_home, '..'))

    # copy sample main.py

    copyfile(os.path.join(os.path.dirname(os.path.dirname(__file__)),
             template_base, 'main-sample.py'),
             os.path.join(project_home, 'main.py'))

    copyfile(os.path.join(os.path.dirname(os.path.dirname(__file__)),
             template_base, 'settings-sample.py'),
             os.path.join(project_home, 'settings.py'))

    copyfile(os.path.join(os.path.dirname(os.path.dirname(__file__)),
             template_base, 'routes-sample.yaml'),
             os.path.join(project_home, 'routes.yaml'))
    # create the eclipse project file

    if create_eclipse_proj:
        create_eclipse_project(project_home, project_name)

    print 'The "%s" project has been created.' % project_name


def commandline():
    if len(sys.argv) > 1:
        main(sys.argv[1:])
    else:
        print usage(sys.argv[0])


# paster version of command, not used yet

try:
    from paste.script import command
    import optparse


    class GaeoCommand(command.Command):

        """Create GAEO project
    
        Example usage::
    
        $ paster gaeo [project name] [--zip] [--eclipse]
        """

        max_args = 3
        min_args = 1
        summary = __doc__.splitlines()[0]
        usage = '\n' + __doc__
        group_name = 'GAEO'

        parser = command.Command.standard_parser(verbose=True)
        parser = \
            optparse.OptionParser(usage='paster gaeo [project name] [--zip] [--eclipse]'
                                  )

        def command(self):
            self.__dict__.update(self.options.__dict__)
            main(self.args)

except:

    pass

if __name__ == '__main__':
    commandline()

