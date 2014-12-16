#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# logging_page.py - Copyright (C) 2012 Red Hat, Inc.
# Written by Fabian Deutsch <fabiand@redhat.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301, USA.  A copy of the GNU General Public License is
# also available at http://www.gnu.org/copyleft/gpl.html.
"""
Configure Logging
"""
import gettext
_ = lambda m: gettext.dgettext(message=m, domain='ovirt-engine-setup')


from ovirt.node import plugins, valid, ui
from TUI_startup.util import valid
from TUI_startup import util as utils
from TUI_startup.model import defaults
from ovirt.node.plugins import Changeset
import inspect
import re

from datetime import datetime

import time
import subprocess
import licenseimport.license_util.des as des
import licenseimport.license_util.md5 as md5
import licenseimport.license_util.get_hardwareid as get_hardwareid
import string
from ovirt_engine_setup.engine import constants as oenginecons

desKey="guofu123"



class AdvanceOptionsDialog(ui.Dialog):
    plugin = None
    _model = [("virtulization", "Virtul"),
              ("gluster", "Gluster"),
              ("both", "Both")
              ]
    _iso_domain = [("yes","Yes"),
                   ("no","No")
                   ]
    model = {
            'OVESETUP_CONFIG_APPLICATION_MODE':'Both'
        }
 
    def __init__(self, plugin,iface):
        super(AdvanceOptionsDialog, self).__init__("dialog.options",iface,[])
        self.plugin = plugin
        
        #padd = lambda l: l.ljust(14)
        ws = [ui.Options("OVESETUP_CONFIG_APPLICATION_MODE","App modes:", self._model),
              
              ui.Options("NFS_CONFIG_ENABLED","NFS ISO Domain:",self._iso_domain),
              ui.Entry("NFS_MOUNT_POINT", "Local ISO domain path [/var/lib/exports/iso]",enabled=True),
              ui.Entry("ISO_DOMAIN_ACL", "Local ISO domain ACL - note that the default will restrict access to localhost.localdomain only, for security reasons [localhost.localdomain(rw)]",enabled=True),
              ui.Entry('ISO_DOMAIN_NAME', "Local ISO domain name [ISO_DOMAIN]",
              enabled=True),
 


              ui.Divider("divider[1]"),

 
              ]
 
        self.plugin.model().update(self.model)
        self.plugin.widgets.add(ws)
        self.children = ws
        self.buttons = [ui.SaveButton("dialog.options.save", "Apply"),
                        ui.CloseButton("dialog.options.close", "Cancel"),
                        ]
        self._dbenvkeys=oenginecons.Const.DEFAULT_ENGINE_DB_ENV_KEYS


overall_config={}
advanced_config={}
class Plugin(plugins.NodePlugin):
    _model = None
    def __init__(self,app):
        super(Plugin, self).__init__(app)

        self.engine_config = defaults.EngineSetup(overall_config,plugin=self)


    def name(self):
        return "Logging"

    def rank(self):
        return 50

    def model(self):
        model = {
            "OVESETUP_CONFIG_WEBSOCKET_PROXY": "yes",
            "OVESETUP_UPDATE_FIREWALL": "no",
            'OVESETUP_CONFIG_FIREWALL_MANAGER':'',
            'OVESETUP_NETWORK_FQDN':'localhost.localdomain',
            'OVESETUP_APACHE_CONFIG_SSL':'Automatic',
            'OVESETUP_PROVISIONING_POSTGRES_LOCATION':'Local' ,
            'OVESETUP_ENGINE_ENABLE':'yes',
            'OVESETUP_CONFIG_WEAK_ENGINE_PASSWORD':'yes',
            'OVESETUP_CONFIG_APPLICATION_MODE':'Both',
            'NFS_CONFIG_ENABLED':'no',
            'OVESETUP_CORE_ENGINE_STOP':'yes',
            'OVESETUP_PROVISIONING_POSTGRES_ENABLED':'automatic', 
            'NFS_MOUNT_POINT' : '/var/lib/exports/iso', 
            'ISO_DOMAIN_ACL' : 'localhost.localdomain(rw)', 
            'ISO_DOMAIN_NAME' : 'ISO_DOMAIN', 
            'OVESETUP_DIALOG_CONFIRM_SETTINGS':'yes',
            'OVESETUP_ENGINE_DB_SECURED':'yes',
            'OVESETUP_ENGINE_DB_SECURED_HOST_VALIDATION':'yes',
            'OVESETUP_APACHE_CONFIG_ROOT_REDIRECTION':'yes'

           
        }
        

        return model

    def _validateFQDN(self,fqdn):
        _IPADDR_RE = re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')

        if _IPADDR_RE.match(fqdn):
            return _(
                    '{fqdn} is an IP address and not a FQDN. '
                    'A FQDN is needed to be able to generate '
                    'certificates correctly.'
                ).format(
                    fqdn=fqdn,
                )
            

        if not fqdn:
            return _('Please specify host FQDN')
           
        if len(fqdn) > 1000:
            return _('FQDN has invalid length')
            
        components = fqdn.split('.', 1)
        if len(components) == 1 or not components[0]:
            return _('Host name {fqdn} has no domain suffix').format(
                    fqdn=fqdn,
                )
            
        else:
            _DOMAIN_RE = re.compile(
                flags=re.VERBOSE,
                pattern=r"""
                    ^
                    [A-Za-z0-9\.\-]+
                    \w+
                    $
                """
            )


            if not _DOMAIN_RE.match(components[1]):
                return _('Host name {fqdn} has invalid domain name').format(
                        fqdn=fqdn,
                    )
        return True     
    def chk_admin_password(self,val):

        if not val:
            return "Please Specify a value"
        if not overall_config.get('OVESETUP_CONFIG_ADMIN_SETUP') == val:
            return "Password not matched"
 
    def chk_value(self,val,valid_value):

        if not val:
            return "Please Specify a value"
        func=lambda x : x.lower() in valid_value or "wrong answer"
        return func(val)
    def validators(self):

        def chk_value(val):

            if not val:
                return "Please Specify a value"
        def chk_bool(val):
            if not val:
                return "Please Specify a value"
 
            func=lambda x : x.lower() in ['yes','no'] or "wrong answer" 
            return func(val)
        def chk_auto_manual(val):
            if not val:
                return "Please Specify a value"
 
            func=lambda x : x.lower() in ['automatic','manual'] or "wrong answer"
            return func(val)
        def license_valid(license):
            try:
                licenseDe = des.strdesde(license,desKey)
                licenseName = licenseDe[0:4]
                deadLine = licenseDe[8:16]
                date_now=datetime.now().strftime("%Y%m%d")
                if date_now > deadLine:
                    return _('License is Expired')
                mac = get_hardwareid.get_hardwareid(license)
                #if (licenseName == md5.strmd5(mac)[0:4]):
	        if ( mac == True ):
                    self.vmAmount = licenseDe[4:8]
                    self.deadLine = licenseDe[8:16]
                # print "license key format success"
                    return True
                else:
                    return  True#_('INVALID LICENSE')
            except Exception as e:
                return True#_('License key format error : %s' %e)

        def chk_db_valid(val):
            if overall_config.has_key('OVESETUP_PROVISIONING_POSTGRES_ENABLED') and overall_config['OVESETUP_PROVISIONING_POSTGRES_ENABLED'].lower()=='manual':
                if not val:
                    return "Please Specify a value"
        return {'OVESETUP_CONFIG_WEBSOCKET_PROXY':chk_bool,
                'OVESETUP_UPDATE_FIREWALL': chk_bool,
                #'OVESETUP_CONFIG_FIREWALL_MANAGER' : lambda x : x in self._detected_managers or 'wrong answer'
                'OVESETUP_APACHE_CONFIG_ROOT_REDIRECTION': chk_bool,
                'OVESETUP_APACHE_CONFIG_SSL': chk_auto_manual,
                'OVESETUP_PROVISIONING_POSTGRES_LOCATION' : lambda x : x in ['Local','Remote'] or "wrong answer", 
                'OVESETUP_PROVISIONING_POSTGRES_ENABLED' : lambda x : x.lower() in ['automatic','manual'] or "wrong answer",
                'OVESETUP_ENGINE_ENABLE': lambda x :x.lower() in ['yes','no'] or 'wrong answer',
                'OVESETUP_CONFIG_ADMIN_SETUP':chk_value,
                'OVESETUP_CONFIG_ADMIN_SETUP_COMFIRM':self.chk_admin_password,
                'OVESETUP_CONFIG_WEAK_ENGINE_PASSWORD':chk_value,
                'OVESETUP_CORE_ENGINE_STOP':lambda x :x.lower() in ['yes','no'] or 'wrong answer',
                'NFS_CONFIG_ENABLED':lambda x :x.lower() in ['yes','no'] or 'wrong answer',
                'NFS_MOUNT_POINT' : chk_value, 
                'ISO_DOMAIN_ACL' : chk_value, 
                'ISO_DOMAIN_NAME' : chk_value, 
                'OVESETUP_LICENSE' : license_valid 


                }

    def get_firewall_managers():
        self._detected_managers = [
            m
            for m in self.application.context.environment[osetupcons.ConfigEnv.FIREWALL_MANAGERS]
            if m.selectable() and m.detect()
        ]
        active_managers = [m for m in self._detected_managers if m.active()]

        self._available_managers = (
            active_managers if active_managers
            else self._detected_managers
            ) 

    def ui_content(self):

        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        print 'caller name:', calframe[1][3] 
        ws = [ui.Header("header[0]", "Ovirt Engine Setup"),
              ui.Divider("divider[0]")
              ]


        #for item in self.application.executelist:
        #    item['callback'].send(ws) 

         #   print item    
        ws.extend([
              ui.Entry("OVESETUP_LICENSE", "please Enter Your License",
              enabled=True),
              ui.Divider("divider[1]")

              ])
 
        #ws.extend([
        #      ui.Entry('OVESETUP_UPDATE_FIREWALL', "Do you want Setup to configure the firewall? (Yes, No) [Yes]",
        #      enabled=True),

        #      ])
 

        
        ws.extend([
              ui.PasswordEntry('OVESETUP_CONFIG_ADMIN_SETUP',"Engine admin password:",enabled=True),
              ui.PasswordEntry('OVESETUP_CONFIG_ADMIN_SETUP_COMFIRM',"Comfirm Engine admin password :",enabled=True),
              ])



        page = ui.Page("page", ws)
        self.widgets.add(page)
        self._fp_dialog=AdvanceOptionsDialog(self,'Engine Advance Options:')
        return page

    def on_change(self, changes):

        overall_config.update(changes)
   
    #def on_merge(self,effective_changes):
     #   pass
    def on_merge(self, effective_changes):
        self.logger.debug("Saving configuration page")
        changes = Changeset(self.pending_changes(False))

        #self.engine_config.update(effective_model)
        if changes.contains_any(["dialog.options.save"]):
            '''
            effective_model = Changeset(self.model())
            effective_model.update(effective_changes)
            for key, value in effective_model.items():
                #import pdb
                #pdb.set_trace()
                if key in advanced_config:
                    continue
                else:
                    advanced_config[key] = value
            ''' 
            self._fp_dialog.close()
 
        if changes.contains_any(["action.fetch_options"]):
             
            self._fp_dialog=AdvanceOptionsDialog(self,'Engine Advance Options:')
            
            return self._fp_dialog
 
        if changes.contains_any(["page.save"]):
            #with open('/root/333','a+') as f:
            #    f.writelines("EFFECTIVE_CHANGE IS %s" %self.engine_config.change)
            effective_model = Changeset(self.model())
            effective_model.update(effective_changes)
            txs = utils.Transaction("Network Interface Configuration")
            for key, value in effective_model.items():
                #import pdb
                #pdb.set_trace()
                if key in overall_config:
                    continue
                else:
                    overall_config[key] = value
             
            self.engine_config.update(overall_config)
            self.engine_config.update(advanced_config)
            error=False
            for ws in self.widgets['page'].elements():
                if isinstance(ws,ui.Entry):
                    if self.validators().get(ws.path):
                        if not self.validators()[ws.path](overall_config.get(ws.path)) in [True,None]:
                             
                            self.widgets[ws.path].label(self.widgets[ws.path].label()+'('+self.validators()[ws.path](ws.value())+')')
                            
                            error = True
            if error:
                return self.widgets['page']
            if len(changes.keys()) ==1 and changes.has_key('page.save'): 
                pass
            else: 
                txs += self.engine_config.transaction()

            #test
             
 
            progress_dialog = ui.TransactionProgressDialog("dialog.txs", txs, self)
            progress_dialog.run()
            self.application.context.__dict__.setdefault('TUI_configuration',{}).update(self.engine_config.change)
            #self.application.context.__dict__['TUI_configuration']=self.application.TUI_configuration    
            if len(txs)>0:
                self.application.app_quit() 
