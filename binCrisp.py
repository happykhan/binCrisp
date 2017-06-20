#!/usr/bin/env python
"""
# Created: Sat, 23 Mar 2013 12:43:16 +1000

binCrisp detects CRISPR sequences from whole genomes using pilercr and draws a
presence/absence matrix. 

binCrisp is a simple script to detect CRISPR sequences from whole genome 
sequences using pilercr and produces visulisation matrix of CRISPR regions 
(in svg using svgwrite)

Dependencies include: 
    * Python 2.7+
    * pilercr must be installed and on PATH: http://www.drive5.com/pilercr/
    * svgwrite: https://pypi.python.org/pypi/svgwrite
Be sure these are installed and on your path. 

See USAGE for optional parameters.

binCrisp has one module (at the moment): findcr

findcr
------
findcr is the main module of the script. 
It requires a directory with all the genomes you wish to use and an file name
to name all the output. 

It combines all genomes sequences in input directory and it runs pilercr from the path.
The results from pilercr are summarised and used to draw and presence absence matrix as
svg using svgwrite.

USAGE: python binCrisp.py findcr GenomeDir/ OutputFileName

The -d or --draw2 flag will space out CRISPR results into a grid to easily show presence/
absence. 

USAGE: python binCrisp.py findcr -d GenomeDir/ OutputFileName

binCrisp output will include:
    * <outputname> (text report from binCrisp itself, this defines the CRISPR sequence
	attached to each ID number in the figure at the bottom.)
    * example.txt (text report of output from pilercr)
    * example.svg (SVG Figure with a matrix of presence and absence of unique
      CRISPR sequence.)

See USAGE i.e. "python binCrisp.py findcr -h" for optional parameters.


### CHANGE LOG ### 
2013-06-27 Nabil-Fareed Alikhan <n.alikhan@uq.edu.au>
    * Initial Release
2016-06-12 Nabil-Fareed Alikhan <n-f.alikhan@warwick.ac.uk>
    * Added Pilercr binaries to bin     
    * Fixes for issue #1
"""
import sys, os, traceback, argparse, operator
import time, subprocess, re
from sets import Set
import svgwrite
import random

__author__ = "Nabil-Fareed Alikhan"
__licence__ = "GPLv3"
__version__ = "0.3"
__email__ = "n.alikhan@uq.edu.au"
epi = "Licence: "+ __licence__ +  " by " + __author__ + " <" + __email__ + ">"

def cmpcr(args):
    # NOT FUNCTIONAL. 
    print 'Comparing CR files'
    print args
    set1_handle=open(args.file[0],'r')
    set2_handle=open(args.file[1],'r')
    set1 = Set([])
    set2 = Set([])
    for f in set1_handle.readlines():
        if f.startswith('$'):
            set1.add(f.strip())
    for f in set2_handle.readlines():
        if f.startswith('$'):
            set2.add(f.strip() )
    doop = set1.difference(set2)
    for f in doop:
        print f[1:]
    print len(doop)

def findcr(args):
    print 'Searching for CRs'
    spacers_out = open(args.output,'w')
    allSpace = []
    # Merges all fasta files in input directory to temp.fna 
    with open('temp.fna', 'w') as outfile:
        for root, dirs, files in os.walk(args.dir, topdown=False):
            for name in sorted(files):
                if name.endswith('.fna'):
                    dooz = os.path.join(root, name)
                    with open(dooz) as infile:
                        outfile.write(infile.read())
    # Run pilercr over temp.fna
    try: 
       proc = subprocess.Popen(['pilercr', '-noinfo', '-in', 'temp.fna', '-out', args.output +'.txt' ])
       print proc.communicate()
    except OSError:
        proc = subprocess.Popen(['bin/pilercr', '-noinfo', '-in', 'temp.fna', '-out', args.output +'.txt' ])
        print proc.communicate()
    # Parse pilercr results
    res_handle = open(args.output +'.txt','r')
    SPACEDICT = {}
    cont = True
    SPACEARRAY = [] 
    arraycount = 0
    DRAWARRAY = [] 
    for f in res_handle.readlines():
        if f.startswith("SUMMARY BY SIMILARITY"):
            cont = False
            if len(SPACEARRAY) > 0:
                print SPACEARRAY
                DRAWARRAY.append(SPACEARRAY)
        if f.startswith("Array"):
            arraycount = f.split()[1]
        if f.startswith('>') and cont: 
            if len(SPACEARRAY) > 0:
                print SPACEARRAY
                DRAWARRAY.append(SPACEARRAY)
            doop = ''
            for a in f.split()[1:]:
                doop += a + ' ' 
            SPACEARRAY = ["Array " + arraycount + ' '+ doop]
            
        elif len(f.split()) >=  6 and cont :
            if re.match('[ATGCatgc]+', f.split()[-1]):
                spacers_out.write( f.strip() + '\n')
                if not SPACEDICT.has_key(f.split()[-1]):
                    SPACEDICT[f.split()[-1]] = len(SPACEDICT) + 1 
                SPACEARRAY.append(SPACEDICT[f.split()[-1]])
                allSpace.append('$' + f.split()[-1] + '\n')
    spacers_out.write('\nALL DETECTED SPACER SEQUENCES\n')
    for f in allSpace:
        spacers_out.write( f)
    spacers_out.write('\nSPACER SEQUENCE CORRESPONDING TO SPACER ID IN FIGURE\n')
    sortedDict = sorted(SPACEDICT.iteritems(), key=operator.itemgetter(1))
    for f in sortedDict:
        spacers_out.write('%d\t%s\n' %(f[1], f[0]))
    spacers_out.close()
    # NOT FULLY IMPLEMENTED
    if args.markup != None:
        NEWARRAY = []
        f = open(args.markup,'r')
        for l in f:
            for d in DRAWARRAY:
                check = d[0].split()[-1] 
                if d[0].split()[-1].startswith('n'):
                    check = d[0].split()[-1][1:]
                if check == l.split(',')[0]:
                    if len(l.split(',')[2]) > 0 :
                        d[0] = d[0][0:8] + ' Escherichia coli ' + l.split(',')[2] + ':' + l.split(',')[3]\
                                + ' str. n' +l.split(',')[0]
                    NEWARRAY.append(d)
                    print l
                    print d[0]
        DRAWARRAY = NEWARRAY
    drawcr(DRAWARRAY,args.output, args.draw2)

# Draws SVG figure of CRISPR matrix 
def drawcr(drawarray, out , draw):
    X = len(drawarray)  * 20  +100
    svg_document = svgwrite.Drawing(filename = out + ".svg",size = ("3000px", str(X)+"px"))
    svg_document.add(svg_document.rect(insert = (0, 0), size = ("3000px", str(X) +"px"), \
        stroke_width = "1",stroke = "black", fill = "rgb(255,255,255)"))
    dint = 1
    maxLeft = 0 
    
    for d in drawarray:
        if len(d[0]) > maxLeft:
            maxLeft = len(d[0]) 
        svg_document.add(svg_document.text(d[0], insert = ( 10, 30 +  dint * 20)))
        dint += 1 
    dint = 1 
    for d in drawarray:
        fint = 0
        for f in d[1:]:
            # RANDOM COLOUR GENERATOR 
            random.seed(f)
            golden_ratio_conjugate = 0.618033988749895
            #intseed = random.randint(0, 100255)
            intseed = random.random()
            intseed += golden_ratio_conjugate
            intseed %= 1
            rsv = hsv_to_rgb(intseed, 0.5,0.95)
            if draw: fint = f
            #Draw the CRISPR box
            svg_document.add(svg_document.rect(insert = ( (maxLeft *6) + (fint *25) , 20 + dint*20), size = ("25px", "15px"), \
                stroke_width = "1",stroke = "black", fill = "rgb(%i,%i,%i)"%(rsv[0],rsv[1],rsv[2]) ))
            svg_document.add(svg_document.text(str(f), \
                insert = ( (maxLeft *6) + (fint *25) +4  , 31 + dint*20))) 
            fint += 1
        dint += 1 
    svg_document.save()

# RANDOM COLOUR GENERATOR 
# HSV values in [0..1]
# returns [r, g, b] values from 0 to 255
def hsv_to_rgb(h, s, v):
    h_i = int(h*6)
    f = h*6 - h_i
    p = v * (1 - s)
    q = v * (1 - f*s)
    t = v * (1 - (1 - f) * s)
    if h_i == 0: r, g, b = v, t, p
    if h_i == 1: r, g, b = q, v, p
    if h_i == 2: r, g, b = p, v, t
    if h_i == 3: r, g, b = p, q, v
    if h_i == 4: r, g, b = t, p, v 
    if h_i == 5: r, g, b = v, p, q
    return [int(r*256), int(g*256), int(b*256)]


def main ():

    global args
    # Find CRISPR seqs. 
        # Given file list, run PilerCR
        # Load spacer list. 
        # Write to file

    # Compare crispr lists - diff

if __name__ == '__main__':
    try:
        start_time = time.time()
        desc = __doc__.split('\n\n')[1].strip()
        parser = argparse.ArgumentParser(description=desc,epilog=epi)
        parser.add_argument ('-v', '--verbose', action='store_true', default=False, help='verbose output')
        parser.add_argument('--version', action='version', version='%(prog)s ' + __version__)
        subparsers = parser.add_subparsers(help='commands')
        find_parser = subparsers.add_parser('findcr', help='Locates CRISPRS given a dir')
        find_parser.add_argument('dir', action='store', help='Directory of genomes')
        find_parser.add_argument ('-v', '--verbose', action='store_true', default=False, help='verbose output')
        find_parser.add_argument ('-d', '--draw2', action='store_true', default=False, help='Draw alternate mode')
        find_parser.add_argument('output',action='store',help='output file')
        find_parser.add_argument('-m', '--markup',action='store',help='annotation file (do not use)')
#        cmp_parser = subparsers.add_parser('cmpcr', help='Compares results. Diff.') 
#        cmp_parser.add_argument('file', action='store', nargs=2, help='Crispr results')
#        cmp_parser.add_argument ('-v', '--verbose', action='store_true', default=False, help='verbose output')
#        cmp_parser.set_defaults(func=cmpcr)
        find_parser.set_defaults(func=findcr)
        args = parser.parse_args()
        if args.verbose: print "Executing @ " + time.asctime()
        args.func(args)
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

