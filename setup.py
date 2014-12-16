from distutils.core import setup
from distutils import filelist
import os
import shutil

import os
from distutils.core import setup
from distutils.command.install_lib import install_lib
from distutils.command.build_py import build_py

from distutils import log
from distutils.dep_util import newer
from py_compile import compile

import os
import sys
from glob import glob

class build_py(build_py):
    def get_module_outfile(self, build_dir, package, module):
        #if 'plugin' in list(package)[0]:
        #    outfile_path = [build_dir] + list(package) + [module + ".py"]

        #else: 
        outfile_path = [build_dir] + list(package) + [module + ".pyc"]
        return os.path.join(*outfile_path)

    def run(self):
        # XXX copy_file by default preserves atime and mtime.  IMHO this is
        # the right thing to do, but perhaps it should be an option -- in
        # particular, a site administrator might want installed files to
        # reflect the time of installation rather than the last
        # modification time before the installed release.

        # XXX copy_file by default preserves mode, which appears to be the
        # wrong thing to do: if a file is read-only in the working
        # directory, we want it to be installed read/write so that the next
        # installation of the same module distribution can overwrite it
        # without problems.  (This might be a Unix-specific issue.)  Thus
        # we turn off 'preserve_mode' when copying to the build directory,
        # since the build directory is supposed to be exactly what the
        # installation will look like (ie. we preserve mode when
        # installing).

        # Two options control which modules will be installed: 'packages'
        # and 'py_modules'.  The former lets us work with whole packages, not
        # specifying individual modules at all; the latter is for
        # specifying modules one-at-a-time.

        if self.py_modules:
            self.build_modules()
        if self.packages:
            self.build_packages()
            self.build_package_data()

    def find_package_modules(self, package, package_dir):
        self.check_package(package, package_dir)
        print package_dir
        #if '_plugin' in package_dir:
        #    module_files = glob(os.path.join(package_dir, "*.py"))
        #else:
        module_files = glob(os.path.join(package_dir, "*.pyc"))
        modules = []
        setup_script = os.path.abspath(self.distribution.script_name)

        for f in module_files:
            abs_f = os.path.abspath(f)
            if abs_f != setup_script:
                module = os.path.splitext(os.path.basename(f))[0]
                modules.append((package, module, f))
            else:
                self.debug_print("excluding %s" % setup_script)
        return modules

 
class InstallLib(install_lib):
    def install(self):
        print self.build_dir
        for root, dirs, files in os.walk(self.build_dir):
            current = root.replace(self.build_dir, self.install_dir)
            for i in dirs:
                self.mkpath(os.path.join(current, i))
            for i in files:
                if os.path.basename(i) == 'setup.py':
                    continue
 
                if not os.path.splitext(i)[1] =='.py' and not os.path.splitext(i)[1] == '.pyc':
                    continue
                file = os.path.join(root, i)
                if os.path.splitext(i)[1] == '.pyc':
                    cfile = os.path.join(current, i)    
                else:
                    cfile = os.path.join(current, i) + "c"
                cfile_base = os.path.basename(cfile)
                #if self.force: #or newer(file, cfile):
                    
                #    log.info("byte-compiling %s to %s", file, cfile_base)
                if os.path.splitext(i)[1] == '.pyc':
                    print cfile
                    self.copy_file(file,cfile, preserve_mode=0)

                    #shutil.copy(file,cfile)
                    print cfile
                        
                else:
                    compile(file, cfile)
                    #shutil.copy(cfile, file+'c')
                    #self.copy_file(cfile, file+'c')



                #else:
                #    log.debug("skipping byte-compilation of %s", file)


setup(
name = "TUI_dialog",  
#cmdclass={"install_lib": InstallLib,'build_py':build_py},
version="1.0",
#ipackage_data={'licenseimport/license_util': ['license_run.pyc']},
packages = ['TUI_plugin','TUI_startup/ovirtnode','TUI_startup/config','TUI_plugin/TUI','dialog_plugin','dialog_plugin/dialog','TUI_startup','TUI_startup/core','TUI_startup/core/engine_setup','TUI_startup/model','TUI_startup/util','TUI_startup/app','TUI_startup/app/ui'],
#data_files=[('licenseimport/license_util', ['license_run'])],
#package_data={'.':['__init__.pyc','des.pyc','get_hardwareid.pyc','license_run.py','md5.pyc']}
#py_modules=['__init__','des','get_hardwareid','license_run','md5']

)
 
