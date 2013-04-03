#!/usr/bin/env python

""" GAEO View module. 

Classes:
    View: Base view interface.
    DjangoTemplateView: 
"""

import re
import os

# gaeo imports
from gaeo import utils

# App imports
import settings

class View(object):
    """ 
    Base view class
    """
    
    def __init__(self, controller):
        self._controller = controller
        
    def render(self):
        raise NotImplementedError('The render method has not been implemented.')
    
    
class AppengineTemplateView(View):
    
    """ This view is implemented by using appengine's template. """
    
    __view_options = {
        'folder': '',
        'script': '',
        'ext': '.html'
    }
    
    def __init__(self, controller, template_path=settings.TEMPLATE_PATH):
        super(AppengineTemplateView, self).__init__(controller)
        self._template_path = template_path
        
    def render(self, data=None, **kwds):
        # get template
        template = self.__init_template()
        
        # merge
        response_data = data if data else {}
        response_data.update(self.__dict__)
        params = self._controller.params
        
        opt = self.__view_options
        
        folder = utils.select_trusy(opt['folder'], params['controller'])
        script = utils.select_trusy(opt['script'], params['action'])
        
        path = os.path.join(self._template_path, 
                            folder,
                            script + opt['ext'])
        self._controller.response.out.write(template.render(path, response_data))
    
    def set_render_path(self, folder='', script='', ext='.html'):
        self.options.update({
            'folder': utils.select_trusy(folder, self.options['folder']),
            'script': utils.select_trusy(script, self.options['script']),
            'ext': utils.select_trusy(ext, self.options['ext'])
        })
    
    @property
    def options(self):
        return self.__view_options

    def __init_template(self):
        """Pre-process the template module like register filters.

        Return
            The processed template module.
        """
        from google.appengine.ext.webapp import template

        # GAEO-provided filters
        cur_dir = os.path.dirname(__file__)
        dirs = [{
            'package': 'gaeo.view.filters', 
            'path': os.path.join(cur_dir, 'filters')
        }]

        # check custom filters, inspired from Issue #54
        custom_filters_path = getattr(settings, 'PLUGIN_FILTERS_PATH')
        if custom_filters_path and os.path.exists(custom_filters_path):
            dirs.append({
                'package': '%s.%s' % (settings.PLUGIN_DIR, settings.PLUGIN_FILTERS_DIR), 
                'path': custom_filters_path
            })

        # register filters
        for d in dirs:
            filters = os.listdir(d['path'])
            for f in filters:
                if not re.match('^__|^\.|.*pyc$', f):
                    module = '%s.%s' % (d['package'], f.replace('.py', ''))
                    template.register_template_library(module)

        return template