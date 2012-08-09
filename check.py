#!/usr/bin/env python
#
# Author: Francois Ingelrest

import commands, eyeD3, os, sys


COVER_MIN_WIDTH  = 400
COVER_MIN_HEIGHT = 400

MIN_CBR = 192
MIN_VBR = 192


if len(sys.argv) < 2:
    print 'USAGE: %s [-s] TOP_DIRECTORY' % os.path.basename(sys.argv[0])
    print
    print 'OPTIONS:'
    print '    -s   Strict mode: Only CBR 320 MP3 files allowed'
    sys.exit(1)



def isLowResCover(file):
    """  """
    (w, h) = commands.getoutput("identify -format \"%%w %%h\" \"%s\"" % file).split()

    return int(w) < COVER_MIN_WIDTH or int(h) < COVER_MIN_HEIGHT



def checkFiles(directory, files, strictMode):
    """ Sanity check for the given files """
    noCover        = True
    lowResCover    = True
    wrongCoverPath = False

    notMP3        = False
    invalidMP3    = False
    nbLowVBRMP3   = 0
    lowBitrateMP3 = False

    for path, file in [(f, os.path.basename(f)) for f in files]:

        # Start with the cover
        if file == 'cover.jpg':

            noCover     = False
            lowResCover = isLowResCover(path)

            continue

        (name, ext) = os.path.splitext(file)

        # Except 'cover.jpg', only .mp3 files are allowed
        if ext != '.mp3':
            notMP3 = True
            continue

        # Check the bitrate
        try:
            audio         = eyeD3.Mp3AudioFile(path)
            mode, bitrate = audio.getBitRate()

            if strictMode:
                if mode != 0 and bitrate < 320:
                    lowBitrateMP3 = True
                else:
                    if mode == 0 and bitrate < MIN_CBR:
                        lowBitrateMP3 = True
                    elif mode == 1 and bitrate < MIN_VBR:
                        nbLowVBRMP3 += 1

        except:
            invalidMP3 = True


    # When an album is split into multiple discs, the cover must be in the parent directory
    if os.path.split(directory)[1].startswith('Disc '):
        if noCover:
            coverPath = os.path.join(os.path.split(directory)[0], 'cover.jpg')

            if os.path.exists(coverPath):
                noCover     = False
                lowResCover = isLowResCover(coverPath)
        else:
            wrongCoverPath = True


    # Resume identified problems
    if noCover or lowResCover or wrongCoverPath or notMP3 or lowBitrateMP3 or nbLowVBRMP3 != 0 or invalidMP3:
        print directory
        print

        if noCover:
            print '    No "cover.jpg" found'
        elif lowResCover:
            print '    The cover has a low resolution (min is %ux%u)' % (COVER_MIN_WIDTH, COVER_MIN_HEIGHT)

        if wrongCoverPath:
            print '    The cover must be located in the parent directory (multiple discs)'

        if notMP3:
            print '    Non-MP3 files found'

        if lowBitrateMP3:
            print '    Low bitrate'

        if nbLowVBRMP3 / float(len(files)) > 0.25:
            print '    Too many low bitrate VBR files'

        if invalidMP3:
            print '    The bitrate could not be read for some files'

        print
        print '---'
        print

        return True

    return False



# Strict mode?
if sys.argv[1] == '-s':
    strictMode = True
    stack      = [sys.argv[2]]
else:
    strictMode = False
    stack      = [sys.argv[1]]

nbProblems = 0

while len(stack) != 0:

    skip      = False
    files     = []
    directory = stack.pop()

    for filename in [os.path.join(directory, f) for f in sorted(os.listdir(directory), reverse=True)]:

        # Split contents into directories and files
        if os.path.isdir(filename):
            stack.append(filename)

            if os.path.split(filename)[1].startswith('Disc '):
                skip = True

        else:
            files.append(filename)

    # If there are some files, check they comply to our rules
    if len(files) != 0 and not skip:
        if checkFiles(directory, files, strictMode):
            nbProblems += 1


print
print 'Found %u problems' % nbProblems
print
