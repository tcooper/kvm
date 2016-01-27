#!/opt/rocks/bin/python
#
# @Copyright@
#
# 				Rocks(r)
# 		         www.rocksclusters.org
# 		         version 6.2 (SideWinder)
#
# Copyright (c) 2000 - 2014 The Regents of the University of California.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# 1. Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
# notice unmodified and in its entirety, this list of conditions and the
# following disclaimer in the documentation and/or other materials provided
# with the distribution.
#
# 3. All advertising and press materials, printed or electronic, mentioning
# features or use of this software must display the following acknowledgement:
#
# 	"This product includes software developed by the Rocks(r)
# 	Cluster Group at the San Diego Supercomputer Center at the
# 	University of California, San Diego and its contributors."
#
# 4. Except as permitted for the purposes of acknowledgment in paragraph 3,
# neither the name or logo of this software nor the names of its
# authors may be used to endorse or promote products derived from this
# software without specific prior written permission.  The name of the
# software includes the following terms, and any derivatives thereof:
# "Rocks", "Rocks Clusters", and "Avalanche Installer".  For licensing of
# the associated name, interested parties should contact Technology
# Transfer & Intellectual Property Services, University of California,
# San Diego, 9500 Gilman Drive, Mail Code 0910, La Jolla, CA 92093-0910,
# Ph: (858) 534-5815, FAX: (858) 534-7345, E-MAIL:invent@ucsd.edu
#
# THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS''
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# @Copyright@
#
#

import os.path

import rocks.commands
import rocks.db.vmextend


class Command(rocks.commands.list.host.command):
    """
    Lists the vnc connection parameters of each vm

    <arg optional='1' type='string' name='host' repeat='1'>
    Zero, one or more host names. If no host names are supplied,
    information for all hosts will be listed.
    </arg>

    <example cmd='list host vm vnc compute-0-0'>
    List the vnc settings for for compute-0-0.
    </example>

    """

    def run(self, params, args):

        (showpassword,) = self.fillParams([('showpassword', 'n')])
        showpassword = self.str2bool(showpassword)

        self.beginOutput()

    #
    # one query does it all!!
    # with preload we specify all the sub fields that we will use
    # and we fetch all the data we need with one big query
    #
    for host in self.newdb.getNodesfromNames(args,
                                             preload=['vm_defs']):

        if not host.vm_defs:
            continue

        # get the physical node that houses this VM
        physhost = 'None'
        if host.vm_defs.physNode:
            physhost = host.vm_defs.physNode.name

        # spit it out!
        info = [physhost]

        flags = 0

        if showpassword:
            import libvirt
            flags |= libvirt.VIR_DOMAIN_XML_SECURE
            info += rocks.db.vmextend.getGraphics(
                host, flags).split(';')
        else:
            info += rocks.db.vmextend.getGraphics(
                host, flags).split(';')

        self.addOutput(host.name, info)

    header = ['vm-host', 'phys-host',
              'type', 'listen', 'port', 'keymap']

    if showpassword:
        header.append('password')
        header.append('validto')

    self.endOutput(header)

RollName = "kvm"
