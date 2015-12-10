#
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
import rocks.db.mappings.kvm
import random
import string
import sys
sys.path.append('/usr/lib64/python2.' + str(sys.version_info[1]) + '/site-packages')
sys.path.append('/usr/lib/python2.' + str(sys.version_info[1]) + '/site-packages')
import libvirt
import datetime

class Command(rocks.commands.HostArgumentProcessor, rocks.commands.set.command):
	"""
	Add a password to the VNC server of the virtual machine specified.

	The virtual machine may need to be restarted to make this effective.

	<arg type='string' name='host' optional='0'>
	One or more VM host names.
	</arg>

	<param type='string' name='password' optional='0'>
	A string to use for the VNC password for the virtual machine.
	If it is password=random, a random string will be set as the password.
	If it is password=none, it will remove the password.
	</param>

	<param type='int' name='duration' optional='1'>
	The duration (in seconds) to allow use of the specified VNC password.
	If duration is not specified the password will be valid for 3600 seconds.
	</param>

	<example cmd='set host vm vncpasswd compute-0-0-0 password=random'>
	Add a random VNC password for node compute-0-0-0 valid for 3600 seconds.
	</example>

	<example cmd='set host vm vncpasswd compute-0-0-0 password=flake_Cind3r duration=15'>
	Add a random VNC password for node compute-0-0-0 valid for 15 seconds.
	</example>

	<example cmd='set host vm vncpasswd compute-0-0-0 password=none'>
	Remove the VNC password from node compute-0-0-0
	</example>
	"""
        def run(self, params, args):

                (password, duration) = self.fillParams([ ('password', ''), ('duration', '3600') ])		

		if password.lower() == 'random':
			password = ''.join(
				random.SystemRandom().choice(
				string.ascii_uppercase + 
				string.ascii_lowercase + 
				string.digits) for _ in range(16))

                nodes = self.newdb.getNodesfromNames(args, managed_only=1, 
			preload=['vm_defs', 'vm_defs.physNode'])

                nodes = self.newdb.getNodesfromNames(args, preload=['vm_defs'])
                if len(nodes) < 1:
                        self.abort('must supply host')

                for node in nodes:
                        if not node.vm_defs:
                                self.abort("node %s is not a virtual node" \
                                                % node.name)

		# Generate a new passwdValidTo string...
		dt1 = datetime.datetime.utcnow()
		dt2 = dt1 + datetime.timedelta(0, int(duration))
		timestr = dt2.strftime("%Y-%m-%dT%H:%M:%S")

                for node in nodes:
                        #
                        # the name of the physical host that will boot
                        # this VM host
                        #
                        if node.vm_defs and node.vm_defs.physNode:
                                #
                                # send the pause command to the physical node
                                #
                                import rocks.vmconstant
				from xml.dom.minidom import parse, parseString

                                hipervisor = libvirt.open(rocks.vmconstant.connectionURL %
                                                        node.vm_defs.physNode.name)
                                domU = hipervisor.lookupByName(node.name)

				# Grab the current XML definition of the domain...
				flags = libvirt.VIR_DOMAIN_XML_SECURE
				domU_xml = parseString(domU.XMLDesc(flags))

				# Parse out the <graphics>...</graphics> device node...
				for gd in domU_xml.getElementsByTagName('graphics'):
					xml = gd.toxml()

				# Modify the passwd and passwdValidUntil fields...
				if password.lower() == 'none':
					if gd.hasAttribute('passwd'):
						gd.removeAttribute('passwd')
					if gd.hasAttribute('passwdValidTo'):
						gd.removeAttribute('passwdValidTo')
				else:
					gd.setAttribute('passwd', password)
					gd.setAttribute('passwdValidTo', timestr)

				# Apply the change to the domain...
				flags = libvirt.VIR_DOMAIN_DEVICE_MODIFY_FORCE | \
					libvirt.VIR_DOMAIN_DEVICE_MODIFY_LIVE
				retval = domU.updateDeviceFlags(gd.toxml(), flags)
				
				# Record setting of vnc password as a boolean host attr
				if password.lower() == 'none':
					self.newdb.setCategoryAttr('host', node.name, \
						'vnc_passwd', 'false')
				else:
					self.newdb.setCategoryAttr('host', node.name, \
						'vnc_passwd', 'true')
                        else:
                                self.abort("virtual host %s does not have a valid physical host" %
                                                node.name)

RollName = "kvm"
