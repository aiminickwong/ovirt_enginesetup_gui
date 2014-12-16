#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# defaults.py - Copyright (C) 2012 Red Hat, Inc.
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

from TUI_startup.util import base, valid
import TUI_startup.util as utils
from TUI_startup.util import exceptions
from TUI_startup.config import network as cnetwork
from TUI_startup.util import fs, storage
import glob
import logging
import os

"""
Classes and functions related to model of the configuration of oVirt Node.

Node is writing it's configuration into one central configuration file
(OVIRT_NODE_DEFAULTS_FILENAME) afterwards all actual configurations files are
created based on this file. This module provides an high level to this model.

There are classes for all components which can be configured through that
central configuration file.
Each class (for a component) can have a configure and apply_config method. Look
at the NodeConfigFileSection for more informations.

Each class should implement a configure method, mainly to define all the
required arguments (or keys).
"""

LOGGER = logging.getLogger(__name__)

OVIRT_NODE_DEFAULTS_FILENAME = "/etc/default/ovirt"

class EngineSetup(object):    
    
    def __init__(self,result,plugin=None):
        self.result=result
        self.plugin=plugin
        self.change={}
    def update(self,change):
        
        self.change.update(change)


    def transaction(self):
        """Return all transactions to re-configure networking
        """
        services = ["network", "ntpd", "ntpdate", "rpcbind", "nfslock",
                    "rpcidmapd", "rpcgssd"]

        def do_services(cmd, services):
            with console.CaptureOutput():
                
                #with open('/root/111','a+') as f:
                self.plugin.application.context.__dict__.setdefault('TUI_configuration',{}).update(self.change) 
                    #f.writelines("SAVED CHANGE  is :%s\n " %self.change)
                print services

  
        class Saving_websocket_proxy(utils.Transaction.Element):
            title = ""
            def commit(self):
                do_services("stop", services)
        
        tx = utils.Transaction("Applying new network configuration")
        tx += [Saving_websocket_proxy()]

        return tx



class SimpleProvider(base.Base):
    """SimpleProvider writes simple KEY=VALUE (shell-like) configuration file

    >>> fn = "/tmp/cfg_dummy.simple"
    >>> open(fn, "w").close()
    >>> cfg = {
    ... "IP_ADDR": "127.0.0.1",
    ... "NETMASK": "255.255.255.0",
    ... }
    >>> p = SimpleProvider(fn)
    >>> p.get_dict()
    {}
    >>> p.update(cfg, True)
    >>> p.get_dict() == cfg
    True
    """
    def __init__(self, filename):
        super(SimpleProvider, self).__init__()
        self.filename = filename
        self.logger.debug("Using %s" % self.filename)

    def update(self, new_dict, remove_empty):
        cfg = self.get_dict()
        cfg.update(new_dict)

        for key, value in cfg.items():
            self.logger.debug("updating configuration : %s = %s " % (key,value))
            if remove_empty and value is None:
                del cfg[key]
            if value is not None and type(value) not in [str, unicode]:
                raise TypeError("The type (%s) of %s is not allowed" %
                                (type(value), key))
        self._write(cfg)

    def get_dict(self):
        with open(self.filename) as source:
            cfg = self._parse_dict(source)
        return cfg

    def _parse_dict(self, source):
        """Parse a simple shell-var-style lines into a dict:

        >>> import StringIO
        >>> txt = "# A comment\\n"
        >>> txt += "A=ah\\n"
        >>> txt += "B=beh\\n"
        >>> txt += "C=\\"ceh\\"\\n"
        >>> txt += "D=\\"more=less\\"\\n"
        >>> p = SimpleProvider("/tmp/cfg_dummy")
        >>> sorted(p._parse_dict(StringIO.StringIO(txt)).items())
        [('A', 'ah'), ('B', 'beh'), ('C', 'ceh'), ('D', 'more=less')]
        """
        cfg = {}
        for line in source:
                if line.startswith("#"):
                    continue
                key, value = line.split("=", 1)
                cfg[key] = value.strip("\"' \n")
        return cfg

    def _write(self, cfg):
        lines = []
        # Sort the dict, looks nicer
        for key in sorted(cfg.iterkeys()):
            lines.append("%s=%s" % (key, cfg[key]))
            self.logger.debug("writing configuration : %s = %s" % (key,cfg[key]))
        contents = "\n".join(lines) + "\n"

        # The following logic is mainly needed to allow an "offline" testing
        config_fs = fs.Config()
        if config_fs.is_enabled():
            with config_fs.open_file(self.filename, "w") as dst:
                dst.write(contents)
        else:
            try:
                self.logger.debug("configuration filename : %s", self.filename)
                fs.atomic_write(self.filename, contents)
            except Exception as e:
                self.logger.warning("Atomic write failed: %s" % e)
                with open(self.filename, "w") as dst:
                    dst.write(contents)


class ConfigFile(base.Base):
    """ConfigFile is a specififc interface to some configuration file with a
    specififc syntax
    """
    def __init__(self, filename=None, provider_class=None):
        super(ConfigFile, self).__init__()
        filename = filename or OVIRT_NODE_DEFAULTS_FILENAME
        provider_class = provider_class or SimpleProvider
        self.provider = provider_class(filename)

    def update(self, new_dict, remove_empty=False):
        """Reads /etc/defaults/ovirt and creates a dictionary
        The dict will contain all OVIRT_* entries of the defaults file.

        Args:
            new_dict: New values to be used for setting the defaults
            filename: The filename to read the defaults from
            remove_empty: Remove a key from defaults file, if the new value
                          is None
        Returns:
            A dict
        """
        self.logger.debug("Updating defaults: %s" % new_dict)
        self.logger.debug("Removing empty entries? %s" % remove_empty)
        self.provider.update(new_dict, remove_empty)

    def get_dict(self):
        return self.provider.get_dict()


class NodeConfigFileSection(base.Base):
    none_value = None
    keys = []

    def __init__(self, cfgfile=None):
        super(NodeConfigFileSection, self).__init__()
        self.defaults = cfgfile or ConfigFile()

    def update(self, *args, **kwargs):
        """This function set's the correct entries in the defaults file for
        that specififc subclass.
        Is expected to call _map_config_and_update_defaults()
        """
        raise NotImplementedError

    def transaction(self):
        """This method returns a transaction which needs to be performed
        to activate the defaults config (so e.g. update cfg files and restart
        services).

        This can be used to update the UI when the transaction has many steps
        """
        raise NotImplementedError

    def commit(self, *args, **kwargs):
        """This method updates the to this subclass specific configuration
        files according to the config keys set with configure.

        A shortcut for:
        tx = obj.ransaction()
        tx()
        """
        tx = self.transaction()
        tx()

    def _args_to_keys_mapping(self, keys_to_args=False):
        """Map the named arguments of th eupdate() method to the CFG keys

        Returns:
            A dict mapping an argname to it's cfg key (or vice versa)
        """
        func = self.update.wrapped_func
        varnames = func.func_code.co_varnames[1:]
        assert len(varnames) == len(self.keys)
        mapping = zip(self.keys, varnames) if keys_to_args else zip(varnames,
                                                                    self.keys)
        return dict(mapping)

    def retrieve(self):
        """Returns the config keys of the current component

        Returns:
            A dict with a mapping (arg, value).
            arg corresponds to the named arguments of the subclass's
            configure() method.
        """
        keys_to_args = self._args_to_keys_mapping(keys_to_args=True)
        cfg = self.defaults.get_dict()
        model = {}
        for key in self.keys:
            value = cfg[key] if key in cfg else self.none_value
            model[keys_to_args[key]] = value
        assert len(keys_to_args) == len(model)
        return model

    def clear(self):
        """Remove the configuration for this item
        """
        cfg = self.defaults.get_dict()
        #to_be_deleted = {k: None for k in self.keys}
        to_be_deleted = dict((k, None) for k in self.keys)
	cfg.update(to_be_deleted)
        self.defaults.update(cfg, remove_empty=True)

    def _map_config_and_update_defaults(self, *args, **kwargs):
        assert len(args) == 0
        assert (set(self.keys) ^ set(kwargs.keys())) == set(), \
            "Keys: %s, Args: %s" % (self.keys, kwargs)
        #new_dict = {k.upper(): v for k, v in kwargs.items()}
        new_dict = dict((k.upper(), v) for k, v in kwargs.items())
	self.defaults.update(new_dict, remove_empty=True)

    @staticmethod
    def map_and_update_defaults_decorator(func):
        """
        FIXME Use some kind of map to map between args and env_Vars
              this would alsoallow kwargs

        >>> class Foo(object):
        ...     keys = None
        ...     def _map_config_and_update_defaults(self, *args, **kwargs):
        ...         return kwargs
        ...     @NodeConfigFileSection.map_and_update_defaults_decorator
        ...     def meth(self, a, b, c):
        ...         assert type(a) is int
        ...         assert type(b) is int
        ...         return {"OVIRT_C": "c%s" % c}
        >>> foo = Foo()
        >>> foo.keys = ("OVIRT_A", "OVIRT_B", "OVIRT_C")
        >>> foo.meth(1, 2, 3)
        {'OVIRT_A': 1, 'OVIRT_B': 2, 'OVIRT_C': 'c3'}
        """
        def wrapper(self, *args, **kwargs):
            if kwargs:
                # if kwargs are given it is interpreted as an update
                # so existing values which are not given in the kwargs are kept
                arg_to_key = self._args_to_keys_mapping()
                update_kwargs = self.retrieve()
                #update_kwargs.update({k: v for k, v in kwargs.items()
                #                      if k in update_kwargs.keys()})
                update_kwargs.update(dict((k, v) for k, v in kwargs.items()
				if k in update_kwargs.keys()))
		kwargs = update_kwargs
                #new_cfg = {arg_to_key[k]: v for k, v in update_kwargs.items()}
		new_cfg = dict((arg_to_key[k], v) for k, v
				in update_kwargs.items())
            else:
                if len(self.keys) != len(args):
                    raise Exception("There are not enough arguments given " +
                                    "for %s of %s" % (func, self))
                new_cfg = dict(zip(self.keys, args))
            custom_cfg = func(self, *args, **kwargs) or {}
            assert type(custom_cfg) is dict, "%s must return a dict" % func
            new_cfg.update(custom_cfg)
            return self._map_config_and_update_defaults(**new_cfg)
        wrapper.wrapped_func = func
        return wrapper


class Network(NodeConfigFileSection):
    """Sets network stuff
    - OVIRT_BOOTIF
    - OVIRT_IP_ADDRESS, OVIRT_IP_NETMASK, OVIRT_IP_GATEWAY
    - OVIRT_VLAN
    - OVIRT_IPV6

    >>> fn = "/tmp/cfg_dummy"
    >>> cfgfile = ConfigFile(fn, SimpleProvider)
    >>> n = Network(cfgfile)
    >>> n.update("eth0", "static", "10.0.0.1", "255.0.0.0", "10.0.0.255",
    ...          "20")
    >>> data = sorted(n.retrieve().items())
    >>> data[:3]
    [('bootproto', 'static'), ('gateway', '10.0.0.255'), ('iface', 'eth0')]
    >>> data[3:]
    [('ipaddr', '10.0.0.1'), ('netmask', '255.0.0.0'), ('vlanid', '20')]

    >>> n.clear()
    >>> data = sorted(n.retrieve().items())
    >>> data[:3]
    [('bootproto', None), ('gateway', None), ('iface', None)]
    >>> data[3:]
    [('ipaddr', None), ('netmask', None), ('vlanid', None)]
    """
    keys = ("OVIRT_BOOTIF",
            "OVIRT_BOOTPROTO",
            "OVIRT_IP_ADDRESS",
            "OVIRT_IP_NETMASK",
            "OVIRT_IP_GATEWAY",
            "OVIRT_VLAN")

    @NodeConfigFileSection.map_and_update_defaults_decorator
    def update(self, iface, bootproto, ipaddr=None, netmask=None, gateway=None,
               vlanid=None):
        if bootproto not in ["static", "none", "dhcp", None]:
            raise exceptions.InvalidData("Unknown bootprotocol: %s" %
                                         bootproto)
        (valid.IPv4Address() | valid.Empty(or_none=True))(ipaddr)
        (valid.IPv4Address() | valid.Empty(or_none=True))(netmask)
        (valid.IPv4Address() | valid.Empty(or_none=True))(gateway)

    def transaction(self):
        """Return all transactions to re-configure networking

        FIXME this should be rewritten o allow more fine grained progress
        informations
        """

        class ConfigureNIC(utils.Transaction.Element):
            title = "Configuring NIC"

            def prepare(self):
                self.logger.debug("Psuedo preparing ovirtnode.Network")

            def commit(self):
                from TUI_startup.ovirtnode.network import Network as oNetwork
                net = oNetwork()
                net.configure_interface()
                net.save_network_configuration()
                #utils.AugeasWrapper.force_reload()

        class ReloadNetworkConfiguration(utils.Transaction.Element):
            title = "Reloading network configuration"

            def commit(self):
                from TUI_startup.util import network 
                utils.AugeasWrapper.force_reload()
                network.reset_resolver()

        tx = utils.Transaction("Applying new network configuration")
        tx.append(ConfigureNIC())
        tx.append(ReloadNetworkConfiguration())
        return tx

    def configure_no_networking(self, iface=None):
        """Can be used to disable all networking
        """
        iface = iface or self.retrieve()["iface"]
        name = iface + "-DISABLED"
        self.update(name, None, None, None, None, None)

    def configure_dhcp(self, iface, vlanid=None):
        """Can be used to configure NIC iface on the vlan vlanid with DHCP
        """
        self.update(iface, "dhcp", None, None, None, vlanid)

    def configure_static(self, iface, ipaddr, netmask, gateway, vlanid):
        """Can be used to configure a static IP on a NIC
        """
        self.update(iface, "static", ipaddr, netmask, gateway, vlanid)


class Hostname(NodeConfigFileSection):
    """Configure hostname
    >>> fn = "/tmp/cfg_dummy"
    >>> cfgfile = ConfigFile(fn, SimpleProvider)
    >>> hostname = "host.example.com"
    >>> n = Hostname(cfgfile)
    >>> n.update(hostname)
    >>> n.retrieve()
    {'hostname': 'host.example.com'}
    """
    keys = ("OVIRT_HOSTNAME",)

    @NodeConfigFileSection.map_and_update_defaults_decorator
    def update(self, hostname):
        (valid.Empty() | valid.FQDNOrIPAddress())(hostname)

    def transaction(self):
        cfg = self.retrieve()
        hostname = cfg["hostname"]

        class UpdateHostname(utils.Transaction.Element):
            title = "Setting hostname"

            def __init__(self, hostname):
                self.hostname = hostname

            def commit(self):
                from TUI_startup.ovirtnode import network as onet
                from TUI_startup.ovirtnode import  ovirtfunctions
                network = onet.Network()

                if self.hostname:
                    network.remove_non_localhost()
                    network.add_localhost_alias(self.hostname)
                else:
                    network.remove_non_localhost()
                    self.hostname = "localhost.localdomain"

                cnetwork.hostname(self.hostname)

                ovirtfunctions.ovirt_store_config("/etc/sysconfig/network")
                ovirtfunctions.ovirt_store_config("/etc/hosts")

                utils.network.reset_resolver()

        tx = utils.Transaction("Configuring hostname")
        tx.append(UpdateHostname(hostname))
        return tx


class Nameservers(NodeConfigFileSection):
    """Configure nameservers
    >>> fn = "/tmp/cfg_dummy"
    >>> cfgfile = ConfigFile(fn, SimpleProvider)
    >>> servers = ["10.0.0.2", "10.0.0.3"]
    >>> n = Nameservers(cfgfile)
    >>> n.update(servers)
    >>> data = n.retrieve()
    >>> all([servers[idx] == s for idx, s in enumerate(data["servers"])])
    True
    >>> n.update([])
    >>> n.retrieve()
    {'servers': None}
    """
    keys = ("OVIRT_DNS",)

    @NodeConfigFileSection.map_and_update_defaults_decorator
    def update(self, servers):
        assert type(servers) is list
        servers = filter(lambda i: i.strip() not in ["", None], servers)
        map(valid.IPv4Address(), servers)
        return {"OVIRT_DNS": ",".join(servers) or None
                }

    def retrieve(self):
        """We mangle the original vale a bit for py convenience
        """
        cfg = dict(NodeConfigFileSection.retrieve(self))
        cfg.update({"servers": cfg["servers"].split(",") if cfg["servers"]
                    else None
                    })
        return cfg

    def transaction(self):
        return self.__legacy_transaction()

    def __legacy_transaction(self):
        class ConfigureNameservers(utils.Transaction.Element):
            title = "Setting namservers"

            def commit(self):
                import ovirtnode.network as onet
                net = onet.Network()
                net.configure_dns()

                utils.network.reset_resolver()

        tx = utils.Transaction("Configuring nameservers")
        tx.append(ConfigureNameservers())
        return tx

    def __new_transaction(self):
        """Derives the nameserver config from OVIRT_DNS

        1. Parse nameservers from defaults
        2. Update resolv.conf
        3. Update ifcfg- (peerdns=no if manual resolv.conf)
        4. Persist resolv.conf

        Args:
            servers: List of servers (str)
        """
        aug = utils.AugeasWrapper()
        ovirt_config = self.defaults.get_dict()

        tx = utils.Transaction("Configuring DNS")

        if "OVIRT_DNS" not in ovirt_config:
            self.logger.debug("No DNS server entry in default config")
            return tx

        servers = ovirt_config["OVIRT_DNS"]
        if servers is None or servers == "":
            self.logger.debug("No DNS servers configured " +
                              "in default config")
        servers = servers.split(",")

        class UpdateResolvConf(utils.Transaction.Element):
            title = "Updating resolv.conf"

            def commit(self):
                # Write resolv.conf any way, sometimes without servers
                comment = ("Please make changes through the TUI. " +
                           "Manual edits to this file will be " +
                           "lost on reboot")
                aug.set("/files/etc/resolv.conf/#comment[1]", comment)
                # Now set the nameservers
                cnetwork.nameservers(servers)
                utils.fs.Config().persist("/etc/resolv.conf")

                utils.network.reset_resolver()

        class UpdatePeerDNS(utils.Transaction.Element):
            title = "Update PEERDNS statement in ifcfg-* files"

            def commit(self):
                # Set or remove PEERDNS for all ifcfg-*
                for nic in glob.glob("/etc/sysconfig/network-scripts/ifcfg-*"):
                    if "ifcfg-lo" in nic:
                        continue
                    path = "/files%s/PEERDNS" % nic
                    if len(servers) > 0:
                        aug.set(path, "no")
                    else:
                        aug.remove(path)

        tx += [UpdateResolvConf(), UpdatePeerDNS()]

        return tx


class Timeservers(NodeConfigFileSection):
    """Configure timeservers

    >>> fn = "/tmp/cfg_dummy"
    >>> cfgfile = ConfigFile(fn, SimpleProvider)
    >>> servers = ["10.0.0.4", "10.0.0.5"]
    >>> n = Timeservers(cfgfile)
    >>> n.update(servers)
    >>> data = n.retrieve()
    >>> all([servers[idx] == s for idx, s in enumerate(data["servers"])])
    True
    >>> n.update([])
    >>> n.retrieve()
    {'servers': None}
    """
    keys = ("OVIRT_NTP",)

    @NodeConfigFileSection.map_and_update_defaults_decorator
    def update(self, servers):
        assert type(servers) is list
        servers = filter(lambda i: i.strip() not in ["", None], servers)
        map(valid.FQDNOrIPAddress(), servers)
        return {"OVIRT_NTP": ",".join(servers) or None
                }

    def retrieve(self):
        cfg = dict(NodeConfigFileSection.retrieve(self))
        cfg.update({"servers": cfg["servers"].split(",") if cfg["servers"]
                    else None
                    })
        return cfg

    def transaction(self):
        return self.__legacy_transaction()

    def __legacy_transaction(self):
        class ConfigureTimeservers(utils.Transaction.Element):
            title = "Setting timeservers"

            def commit(self):
                from TUI_startup.ovirtnode import network as onet
                net = onet.Network()
                net.configure_ntp()
                net.save_ntp_configuration()

        tx = utils.Transaction("Configuring timeservers")
        tx.append(ConfigureTimeservers())
        return tx

