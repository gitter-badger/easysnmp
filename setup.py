import os
import sys
import shlex
try:
    import _winreg
except:
    pass

from setuptools import setup, Extension
from setuptools.command.test import test as TestCommand

# Determine if a base directory has been provided with the --basedir option
in_tree = False
# Add compiler flags if debug is set
if sys.platform != 'win32':
    compile_args = ['-Wno-unused-function']
else:
    compile_args = []

for arg in sys.argv:
    if arg.startswith('--debug'):
        # Note from GCC manual:
        #       If you use multiple -O options, with or without level numbers,
        #       the last such option is the one that is effective.
        if sys.platform != 'win32':
            compile_args.extend('-Wall -O0 -g'.split())
        else:
            compile_args.extend('/Wall /Od /Zi'.split()) # -g seems close to /Zi, but -O0 may not be the same with /Od
    elif arg.startswith('--basedir='):
        basedir = arg.split('=')[1]
        sys.argv.remove(arg)
        in_tree = True

# If a base directory has been provided, we use it
if in_tree:
    netsnmp_libs = os.popen(basedir + os.path.sep + 'net-snmp-config --libs').read()

    libdirs = os.popen('{0}' + os.path.sep + 'net-snmp-config --build-lib-dirs {1}'.format(basedir, basedir)).read()  # noqa
    incdirs = os.popen('{0}' + os.path.sep + 'net-snmp-config --build-includes {1}'.format(basedir, basedir)).read()  # noqa

    libs = [flag[2:] for flag in shlex.split(netsnmp_libs) if flag.startswith('-l')]  # noqa
    libdirs = [flag[2:] for flag in shlex.split(libdirs) if flag.startswith('-L')]    # noqa
    incdirs = [flag[2:] for flag in shlex.split(incdirs) if flag.startswith('-I')]    # noqa

# Otherwise, we use the system-installed SNMP libraries
else:
    if sys.platform != 'win32':
        netsnmp_libs = os.popen('net-snmp-config --libs').read()

        libs = [flag[2:] for flag in shlex.split(netsnmp_libs) if flag.startswith('-l')]     # noqa
        libdirs = [flag[2:] for flag in shlex.split(netsnmp_libs) if flag.startswith('-L')]  # noqa
        incdirs = []
    else:
        # Get Net-SNMP install dir
        snmpkey = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, "Software\\Net-SNMP")
        snmpdir = _winreg.QueryValueEx(snmpkey, "InstallDir")[0]  # + '\\include'

        # Got OpenSSL?
        sslkey = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall")
        
        i = 0
        sslvalue = None
        while True:
            try:
                if 'OpenSSL' in _winreg.EnumKey(sslkey, i):
                    sslkey = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\" + str(_winreg.EnumKey(sslkey,i)))
                    sslvalue = _winreg.QueryValueEx(sslkey, "InstallLocation")[0]
                else:
                    i += 1
            except WindowsError:
                break

        libs = ['libagent', 'libsnmp', 'libnetsnmptrapd', 'netsnmpmibs'] # https://sourceforge.net/p/net-snmp/code/ci/master/tree/win32/Makefile.in#l26
        libdirs = [snmpdir]
        incdirs = [str(snmpdir + '\\include')]
        #netsnmp_libs = os.popen('net-snmp-config --libs').read()

# Setup the py.test class for use with the test command
class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', 'Arguments to pass to py.test')]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # Import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


# Read the long description from readme.rst
try:
    with open('setup.rst') as f:
        long_description = f.read()
except IOError:
    long_description = None


setup(
    name='easysnmp',
    version='0.2.5-dev',
    description='A blazingly fast and Pythonic SNMP library based on the '
                'official Net-SNMP bindings',
    long_description=long_description,
    author='Fotis Gimian',
    author_email='fgimiansoftware@gmail.com',
    url='https://github.com/fgimian/easysnmp',
    license='BSD',
    packages=['easysnmp'],
    tests_require=['pytest-cov', 'pytest-flake8', 'pytest-sugar', 'pytest'],
    cmdclass={'test': PyTest},
    ext_modules=[
        Extension(
            'easysnmp.interface', ['easysnmp/interface.c'],
            library_dirs=libdirs, include_dirs=incdirs, libraries=libs,
            extra_compile_args=compile_args
        )
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: System :: Networking',
        'Topic :: System :: Networking :: Monitoring'
    ]
)
