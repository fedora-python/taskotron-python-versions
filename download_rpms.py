# -*- coding: utf-8 -*-

'''Download correct NVRs for python-versions to operate on.'''

import sys
import logging
from libtaskotron.directives import koji_directive

def download_rpms(koji_build, rpmsdir, arch=['x86_64'], arch_exclude=[],
                  src=True, debuginfo=False, build_log=True):
    '''Download RPMs for a koji build NVR.'''

    koji = koji_directive.KojiDirective()

    print 'Downloading rpms for %s into %s' % (koji_build, rpmsdir)
    params = {'action': 'download',
              'koji_build': koji_build,
              'arch': arch,
              'arch_exclude': arch_exclude,
              'src': src,
              'debuginfo': debuginfo,
              'target_dir': rpmsdir,
              'build_log': build_log,
             }
    arg_data = {'workdir': None}
    koji.process(params, arg_data)

    print 'Downloading complete'


if __name__ == '__main__':
    print 'Running script: %s' % sys.argv
    logging.basicConfig()
    logging.getLogger('libtaskotron').setLevel(logging.DEBUG)
    args = {}

    # arch is supposed to be a comma delimited string, but optional
    arches = sys.argv[3] if len(sys.argv) >= 4 else ''
    arches = [arch.strip() for arch in arches.split(',')]
    if arches:
        print 'Requested arches: %s' % arches
        args['arch'] = arches

    download_rpms(koji_build=sys.argv[1],
                  rpmsdir=sys.argv[2],
                  **args
                  )
