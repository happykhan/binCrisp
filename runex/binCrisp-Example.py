#!/usr/bin/env python
"""
# Created: Mon, 18 Mar 2013 11:57:13 +1000

Quick example test of binCrisp script. Just run 'python binCrisp.py -v'.\
        Requires remote file list. (Default: fas-loc in runex dir)

Dependencies include: 
    * Python 2.7+
    * pilercr must be installed and on PATH: http://www.drive5.com/pilercr/
    * svgwrite: https://pypi.python.org/pypi/svgwrite

binCrisp-Example.py is a quick example test of the binCrisp script.
Just run 'python binCrisp-Example.py -v'. 

It requires reference genes and remote file list. (Default: fas-loc in runex dir).

This script runs an example case for the binCrisp script, based off 11 E. coli
genomes (& E. fergusonii) downloaded from a remote server (listed in fas-loc).

This script should be run from the runex folder in the parent binCrisp dir.
This script will check Dependencies, format input files, and run binCrisp.py

binCrisp output will include:
    * example (text report from binCrisp itself, this defines the CRISPR sequence
	attached to each ID number in the figure at the bottom.)
    * example.txt (text report of output from pilercr)
    * example.svg (SVG Figure with a matrix of presence and absence of unique
      CRISPR sequence.)

Total Runtime: ~3 minutes.

### CHANGE LOG ### 
2013-06-27 Nabil-Fareed Alikhan <n.alikhan@uq.edu.au>
    * v0.3: Intial build
"""
import sys, os, traceback, argparse
import time, gzip, subprocess
import urllib2

__author__ = "Nabil-Fareed Alikhan"
__licence__ = "GPLv3"
__version__ = "0.3"
__email__ = "n.alikhan@uq.edu.au"
epi = "Licence: "+ __licence__ +  " by " + __author__ + " <" + __email__ + ">"

def main ():
    global args

    # CHECK DEPENDENCIES. Dryad requires Biopython, BLAST & MUSCLE to run.
    sys.stdout.write('Testing svgwrite is installed...')
    try:
        import svgwrite
        dwg = svgwrite.Drawing('test.svg', profile='tiny')
    except:
        print '\nERROR: svgwrite is not installed, see <https://pypi.python.org/pypi/svgwrite>'
        exit(1)
    print 'OK!'
    sys.stdout.write('Testing if pilercr is installed (and on PATH)...')
    try:
        subprocess.check_output(['pilercr','-help'])
    except:
        print '\nERROR: pilercr is not installed (Or it is not on your PATH)'
        exit(1)
    print 'OK!'

    # CREATE DIR & DOWNLOAD GENOMES
    if args.verbose: 'Options: %s' %(args)
    print 'Fetching genomes from %s' %(args.genomelist)
    if not os.path.exists('gen/'):
        os.mkdir('gen')
        if args.verbose:  'Creating dir: gen/'
    filelist = open('Example-list', 'w')
    if args.verbose:  'Writing genomes to: gen/'
    with open(args.genomelist, 'r') as gen:
        for gen in gen.readlines():
            genpath = os.path.join('gen/', gen.split('/')[-1].strip() )
            if not os.path.exists(genpath):
                fetchFile(gen,'gen')
            if genpath.endswith('.gz'):
                if args.verbose: print 'Unzipped %s' %(genpath)
                gencom = gzip.open(genpath, 'rb')
                outgbk = genpath[:-3]
                gengbk = open(outgbk, 'wb')
                gengbk.write(gencom.read())
                gencom.close()
                gengbk.close()
                filelist.write('%s\n' %(outgbk))
                os.remove(genpath)
            else:
                filelist.write('%s\n' %(genpath))
    filelist.close()

    # LAUNCH binCrisp SCRIPT
    Crispopts = ['python', '../binCrisp.py', 'findcr',  'gen/', 'example']
    proc = subprocess.Popen(Crispopts)
    print '\nRunning binCrisp script as:\n\n%s %s %s %s %s \n' \
        %('python', '../binCrisp.py', 'findcr',  'gen/', 'example')
    print '===NOW LAUNCHING binCrisp SCRIPT==='
    print proc.communicate()
    print '===binCrisp COMPLETE==='


def fetchFile(url, outdir):

    file_name = url.split('/')[-1]
    u = urllib2.urlopen(url)
    f = open(os.path.join(outdir, file_name.strip()), 'wb')
    meta = u.info()
    file_size = int(meta.getheaders("Content-Length")[0])
    if args.verbose: print "Downloading: %s Bytes: %s" % (file_name, file_size)

    file_size_dl = 0
    block_sz = 8192
    while True:
        buffer = u.read(block_sz)
        if not buffer:
            break

        file_size_dl += len(buffer)
        f.write(buffer)
        status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
        status = status + chr(8)*(len(status)+1)
        if args.verbose: print status,

    f.close()

if __name__ == '__main__':
    try:
        start_time = time.time()
        desc = __doc__.split('\n\n')[1].strip()
        parser = argparse.ArgumentParser(description=desc,epilog=epi)
        parser.add_argument ('-v', '--verbose', action='store_true', default=False, help='verbose output')
        parser.add_argument('--version', action='version', version='%(prog)s ' + __version__)
        parser.add_argument ('-f','--genomelist', default='fas-loc', action='store', help='List of remote locations of genomes [Default: fas-loc]')
        args = parser.parse_args()
        if args.verbose: print "Executing @ " + time.asctime()
        main()
        if args.verbose: print "Ended @ " + time.asctime()
        if args.verbose: print 'total time in minutes:',
        if args.verbose: print (time.time() - start_time) / 60.0
        sys.exit(0)
    except KeyboardInterrupt, e: # Ctrl-C
        raise e
    except SystemExit, e: # sys.exit()
        raise e
    except Exception, e:
        print 'ERROR, UNEXPECTED EXCEPTION'
        print str(e)
        traceback.print_exc()
        os._exit(1)

