# Based on the docker connection plugin
#
# Connection plugin for building container images using buildah tool
#   https://github.com/projectatomic/buildah
#
# Written by: Tomas Tomecek (https://github.com/TomasTomecek)
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import (absolute_import, division, print_function)

import shlex

__metaclass__ = type

# import distutils.spawn
# import os
# import os.path
import subprocess
# import re
# 
# from distutils.version import LooseVersion
# 
import ansible.constants as C
# from ansible.errors import AnsibleError, AnsibleFileNotFound
# from ansible.module_utils.six.moves import shlex_quote
from ansible.module_utils._text import to_bytes, to_native
from ansible.plugins.connection import ConnectionBase, ensure_connect

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


# this _has to be_ named Connection
class Connection(ConnectionBase):
    """
    TBD
    """

    # String used to identify this Connection class from other classes
    transport = 'buildah'
    # TODO: what does pipelining mean?
    has_pipelining = False
    # TODO: it should be possible to change user in the container
    become_methods = frozenset(C.BECOME_METHODS)

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)

        display.v("PLAY_CONTEXT %s" % self._play_context)

        self._container_id = None
        self._connected = False
        # if self._play_context.remote_user is not None:
        # TODO: save actual user

    def _connect(self):
        """ Create a container from specified container image, via host """
        super(Connection, self)._connect()
        # syntax to reference images from docker daemon is:
        #   <docker-daemon:image:tag>
        local_cmd = ['buildah', 'from', '-q', self._play_context.remote_addr]
        local_cmd = [to_bytes(i, errors='surrogate_or_strict') for i in local_cmd]
        p = subprocess.Popen(local_cmd, shell=False, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout, stderr = p.communicate()
        display.vvvvv("STDOUT %s" % (stdout, ))
        if stderr:
            display.vvv("STDERR %s" % (stderr, ), host=self._play_context.remote_addr)
        self._container_id = stdout.strip()
        self._connected = True

    @ensure_connect
    def exec_command(self, cmd, in_data=None, sudoable=False):
        """ Run a command on the docker host """
        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)

        display.v("%s" % self.connected)

        cmd_args_list = shlex.split(cmd)

        local_cmd = ['buildah', 'run', '--', self._container_id]
        local_cmd += cmd_args_list
        local_cmd = [to_bytes(i, errors='surrogate_or_strict') for i in local_cmd]

        display.vvv("RUN %s" % (local_cmd,), host=self._container_id)
        p = subprocess.Popen(local_cmd, shell=False, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout, stderr = p.communicate(in_data)
        # display.vvvvv("STDOUT %s STDERR %s" % (stderr, stderr))
        return (p.returncode, stdout, stderr)

#     def _prefix_login_path(self, remote_path):
#         ''' Make sure that we put files into a standard path
#
#             If a path is relative, then we need to choose where to put it.
#             ssh chooses $HOME but we aren't guaranteed that a home dir will
#             exist in any given chroot.  So for now we're choosing "/" instead.
#             This also happens to be the former default.
#
#             Can revisit using $HOME instead if it's a problem
#         '''
#         if not remote_path.startswith(os.path.sep):
#             remote_path = os.path.join(os.path.sep, remote_path)
#         return os.path.normpath(remote_path)
#
    @ensure_connect
    def put_file(self, in_path, out_path):
        """ Place a local file located in in_path inside container on out_path """
        super(Connection, self).put_file(in_path, out_path)
        display.vvv("PUT %s TO %s" % (in_path, out_path), host=self._play_context.remote_addr)

        local_cmd = ['buildah', 'copy', '--', self._container_id, in_path, out_path]
        local_cmd = [to_bytes(i, errors='surrogate_or_strict') for i in local_cmd]

        display.vvv("RUN %s" % (local_cmd,), host=self._container_id)
        p = subprocess.Popen(local_cmd, shell=False, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout, stderr = p.communicate()

    @ensure_connect
    def fetch_file(self, in_path, out_path):
        pass
#         """ Fetch a file from container to local. """
#         super(Connection, self).fetch_file(in_path, out_path)
#         display.vvv("FETCH %s TO %s" % (in_path, out_path), host=self._play_context.remote_addr)
#
#         in_path = self._prefix_login_path(in_path)
#         # out_path is the final file path, but docker takes a directory, not a
#         # file path
#         out_dir = os.path.dirname(out_path)
#
#         args = [self.docker_cmd, "cp", "%s:%s" % (self._play_context.remote_addr, in_path), out_dir]
#         args = [to_bytes(i, errors='surrogate_or_strict') for i in args]
#
#         p = subprocess.Popen(args, stdin=subprocess.PIPE,
#                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#         p.communicate()
#
#         # Rename if needed
#         actual_out_path = os.path.join(out_dir, os.path.basename(in_path))
#         if actual_out_path != out_path:
#             os.rename(to_bytes(actual_out_path, errors='strict'), to_bytes(out_path, errors='strict'))
#
    def close(self):
        pass
#         """ Terminate the connection. Nothing to do for Docker"""
#         super(Connection, self).close()
#         self._connected = False
