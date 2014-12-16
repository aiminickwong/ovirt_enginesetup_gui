import logging
import gettext
_ = lambda m: gettext.dgettext(message=m, domain='otopi')

import sys
import site
for site in site.getsitepackages():
    if not site in sys.path:
        sys.path.append(site)

import traceback
import gettext
_ = lambda m: gettext.dgettext(message=m, domain='ovirt-engine-setup')


from otopi import util
from otopi import plugin



import inspect
from datetime import datetime



@util.export
class Plugin(plugin.PluginBase):
    """Human dialog protocol provider.

    Environment:
        DialogEnv.DIALECT -- if human activate.
        DialogEnv.BOUNDARY -- set bundary to use.

    """


    def __init__(self, context):
        super(Plugin, self).__init__(context=context)
        self._enabled = True
 
    #pop up a license input dialog
    @plugin.event(
        stage=plugin.Stages.STAGE_CUSTOMIZATION,
        priority=plugin.Stages.PRIORITY_FIRST,
        name="TUI._TUI_startup"
        
    )

    def _TUI_startup(self):
 
        from TUI_startup.__main__ import run
        run(self.context)      





