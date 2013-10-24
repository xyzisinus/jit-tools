#! /usr/bin/python

import os
import sys
import subprocess
import select
import pynotify
import datetime

# I wrote this script to import cds of some long books (more than 40 cds!).
# How to use:
#
# mkdir my-book-title
# cd my-book-title
# python readcd.py first-cd-number [total-number-of-cds]
#
# Then the program will ask you if you are ready to import
# my-book-title-01.mp3 (suppose your first cd number is 1)
#
# or if you give the second argument (optional)
# my-book-title-01-of-44.mp3 (suppose your total number of cds is 44)
#
# When you enter "return" or any character, the cd will be imported into
# the current directory.  When the import is done, your cd will be popped out.
# To avoid accident: Do NOT place anything near the cd bay!
#
# Then the program will ask you if you want to import the next cd.
# Place the next cd into the drive and enter "return". 
# Note: The program may be still busy merging the tracks for the last cd
# imported.  It asks you to insert the next cd early so that it can read the
# cd ASAP.
#
# When you are done with the last cd, use control-c to terminate.
#
# This program uses cdda2ogg which I found is the most tolerant for damaged
# cds.

pynotify.init('readcd')

if (len(sys.argv[1:]) > 1) :
  (startn, totaln) = sys.argv[1:]
else:
  (startn, totaln) = (sys.argv[1], 0)

title = os.path.basename(os.getcwd())
cdn = int(startn)
totaln = int(totaln)

while True:
  if (totaln == 0) :
    disk = title + '-%02d'%cdn + '.mp3'
  else:
    disk = title + '-%02d-of-%02d'%(cdn, totaln) + '.mp3'

  msg = 'Ready to import %s?' % disk
  notice = pynotify.Notification(msg)
  notice.set_timeout(0)
  notice.show()

  print datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), msg
  dummy = raw_input().lower()  # wait for any character from user

  start = datetime.datetime.now()
  p = subprocess.Popen(['cdda2ogg'],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)

  while True:
    reads = [p.stdout.fileno(), p.stderr.fileno()]
    ret = select.select(reads, [], [])

    for fd in ret[0]:
      if fd == p.stdout.fileno():
        read = p.stdout.readline()
        sys.stdout.write('stdout: ' + read)
      if fd == p.stderr.fileno():
        read = p.stderr.readline()
        sys.stderr.write('stderr: ' + read)

    if p.poll() != None:
      break

  # end of poll loop

  end = datetime.datetime.now()
  print 'Disk %s imported in' % disk, end - start
  os.system('eject')
  soxcmd = 'sox *audiotrack.ogg %s' % disk
  rmcmd = 'rm -f *audiotrack.ogg'
  print 'Merge tracks:', soxcmd
  os.system(soxcmd)
  print 'Clean tracks:', rmcmd
  os.system(rmcmd)
  end = datetime.datetime.now()
  print 'Disk %s imported and processed in' % disk, end - start
  
  cdn += 1

#end of disk loop
