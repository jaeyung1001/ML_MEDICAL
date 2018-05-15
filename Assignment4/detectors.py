# -*- coding: utf-8 -*-
#
# This file is part of PyGaze - the open-source toolbox for eye tracking
#
#   PyGazeAnalyser is a Python module for easily analysing eye-tracking data
#   Copyright (C) 2014  Edwin S. Dalmaijer
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>

# EyeTribe Reader
#
# Reads files as produced by PyTribe (https://github.com/esdalmaijer/PyTribe),
# and performs a very crude fixation and blink detection: every sample that
# is invalid (usually coded '0.0') is considered to be part of a blink, and
# every sample in which the gaze movement velocity is below a threshold is
# considered to be part of a fixation. For optimal event detection, it would be
# better to use a different algorithm, e.g.:
# Nystrom, M., & Holmqvist, K. (2010). An adaptive algorithm for fixation,
# saccade, and glissade detection in eyetracking data. Behavior Research
# Methods, 42, 188-204. doi:10.3758/BRM.42.1.188
#
# (C) Edwin Dalmaijer, 2014
# edwin.dalmaijer@psy.ox.ax.uk
#
# version 1 (01-Jul-2014)

__author__ = "Edwin Dalmaijer"

import numpy


def blink_detection(x, y, time, missing=0.0, minlen=10, maxlen=100): 
    """Detects blinks, defined as a period of missing data that lasts for at
    least a minimal amount of samples

    arguments

    x       -   numpy array of x positions
    y       -   numpy array of y positions
    time        -   numpy array of EyeTribe timestamps

    keyword arguments

    missing -   value to be used for missing data (default = 0.0)
    minlen  -   integer indicating the minimal amount of consecutive
                missing samples
    maxlen -    integer indicating the maximal amount of consecutive
                missing samples (125 trials == 1000 ms (micro-sleep))
    
    returns
    missings, Sblk, Eblk, Ablk
                missings -   list of lists, each containing [starttime, endtime, duration] of all missings
                Sblk    -   list of lists, each containing [starttime] of all blinks
                Eblk    -   list of lists, each containing [starttime, endtime, duration] of all blinks
                Ablk    -   list of lists, each containing [endtime] of all blinks
    """
    # empty list to contain data    
    Sblk = []
    Eblk = []
    Ablk = []

    missings = []

    # check where the missing samples are
    miss = (numpy.array(x)==-1) & (numpy.array(y)==-1)
    miss = numpy.array(miss, dtype=int)
    miss = numpy.insert(miss, 0,0)
    # mx = numpy.array(x==missing, dtype=int)
    # my = numpy.array(y==missing, dtype=int)
    
    # check where x and y are missing
    # first element == 0, so that a blink that starts the trial is detected
    # miss = numpy.append([0],numpy.array((mx+my) == 2, dtype=int))
    # print("miss:", miss)
    # check where the starts and ends are

    starts = numpy.where(numpy.diff(miss)==1)[0]
    ends = numpy.where(numpy.diff(miss)==-1)[0]
    # compile blink starts and ends
    for i in range(len(starts)):
        # get starting index
        s = starts[i]
        # get ending index
        if i < len(ends):
            e = ends[i]
        elif len(ends) > 0:
            e = ends[-1]
        else:
            e = -1
            
        # append only if the duration in samples is equal to 
        # or greater than the minimal duration
        if e-s >= minlen:
            missings.append([time[s],time[e],time[e]-time[s]])
            # append only if the duration is less than
            # or equal to the maximum duration
            if e-s <= maxlen:
                # add starting time
                Sblk.append([time[s]])
                # add starting time, ending time, duration
                Eblk.append([time[s],time[e],time[e]-time[s]])
                # add ending time
                Ablk.append([time[e]])

    return missings, Sblk, Eblk, Ablk


def fixation_detection(x, y, time, missing=0.0, maxdist=25, mindur=50, maxdur=600):
    
    """Detects fixations, defined as consecutive samples with an inter-sample
    distance of less than a set amount of pixels (disregarding missing data)
    
    arguments

    x       -   numpy array of x positions
    y       -   numpy array of y positions
    time        -   numpy array of eyetracker timestamps

    keyword arguments

    missing -   value to be used for missing data (default = 0.0)
    maxdist -   maximal inter sample distance in pixels (default = 25)
    mindur  -   minimal duration of a fixation in milliseconds; detected
                fixation cadidates will be disregarded if they are below
                this duration (default = 100)
    maxdur -    maximal duration of a fixation in milliseconds; 
    
    returns
    Sfix, Efix
                Sfix    -   list of lists, each containing [starttime]
                Efix    -   list of lists, each containing [starttime, endtime, duration, endx, endy, dispersion]
    """

    # empty lists to contain data
    Sfix = []
    Efix = []

    # loop through all coordinates
    si = 0
    fixstart = False
    for i in range(1,len(x)):
        # calculate Euclidean distance from the current fixation coordinate
        # to the next coordinate
        dist = ((x[si]-x[i])**2 + (y[si]-y[i])**2)**0.5

        # check if the next coordinate is below maximal distance
        if dist <= maxdist and not fixstart:
            # start a new fixation
            si = 0 + i
            fixstart = True
            # store starting time
            Sfix.append([time[i]])
        elif dist > maxdist and fixstart:
            # end the current fixation
            fixstart = False
            # only store the fixation if the duration is ok
            if time[i-1]-Sfix[-1][0] >= mindur and time[i-1]-Sfix[-1][0] <= maxdur:
                #only store if there are no missings
                if x[i-1] != missing and y[i-1] != missing:
                    # store starting time, ending time, duration, ending x-coordinate, ending y-coordinate, distance from start to end
                    Efix.append([Sfix[-1][0], time[i-1], time[i-1]-Sfix[-1][0], x[si], y[si], ((x[si]-x[i-1])**2 + (y[si]-y[i-1])**2)**0.5])
                else:
                    Sfix.pop(-1)
            # delete the last fixation start if the fixation was too short
            else:
                Sfix.pop(-1)
            si = 0 + i
        elif not fixstart:
            si += 1
    
    return Sfix, Efix


def saccade_detection(x, y, time, missings, missing=0.0, mindur=5, minvel=40, minacc=340):
    
    """Detects saccades, defined as consecutive samples with an inter-sample
    velocity of over a velocity threshold or an acceleration threshold

    arguments

    x       -   numpy array of x positions
    y       -   numpy array of y positions
    time        -   numpy array of tracker timestamps in milliseconds

    keyword arguments

    missing -   value to be used for missing data (default = 0.0)
    mindur  -   minimal duration of saccades in milliseconds; all detected
                saccades with len(sac) < minlen will be ignored
                (default = 5)
    minlen  -   minimum length of a saccade in px
    maxvel  -   velocity threshold in pixels/second (default = 40)
    maxacc  -   acceleration threshold in pixels / second**2
                (default = 340)
    
    returns
    Ssac, Esac
            Ssac    -   list of lists, each containing [starttime]
            Esac    -   list of lists, each containing [starttime, endtime, duration, startx, starty, endx, endy]
    """
    
    # CONTAINERS
    Ssac = []
    Esac = []
    
    # The following code analyses saccades only in areas in between blinks 
    # and also excludes (non-blink) missing data from analysis
    xtemp = []
    ytemp = []
    timetemp = []
    xdata = []
    ydata = []
    timedata = []
    
    # count the amount of areas in between blinks
    count = 0
    # loop through all timestamps of the trial
    for i in range(len(time)):
        if(count<len(missings)):
            # if there is no blink start, append time[i]
            if time[i] != missings[count][0]:
                # do not append missing data 
                if x[i] != missing and y[i] != missing:
                    xtemp.append(x[i])
                    ytemp.append(y[i])
                    timetemp.append(time[i])

            # if there is a blink start, end current array
            # and transfer data to data arrays
            elif time[i] == missings[count][0]:
                xdata.append(xtemp)
                ydata.append(ytemp)
                timedata.append(timetemp)
                
                # clear temp arrays
                xtemp = []
                ytemp = []
                timetemp = []

                # check if count +=1 works here as well

            # if time[i] is a blink end, delete everyting since blink start
            if time[i] == missings[count][1]:
                xtemp = []
                ytemp = []
                timetemp = []

                # set count to the current amount of data arrays in between missings
                count +=1
        else:
            # append every non-missing trial after the last blink ended
            if x[i] != missing and y[i] != missing:
                    xtemp.append(x[i])
                    ytemp.append(y[i])
                    timetemp.append(time[i])

    # append the last array to the data arrays
    xdata.append(xtemp)
    ydata.append(ytemp)
    timedata.append(timetemp)
    
    # remove empty array
    xdata.remove(xdata[0])
    ydata.remove(ydata[0])
    timedata.remove(timedata[0])
    
    for i in range(len(xdata)):

        # INTER-SAMPLE MEASURES
        # the distance between samples is the square root of the sum
        # of the squared horizontal and vertical interdistances
        intdist = (numpy.diff(xdata[i])**2 + numpy.diff(ydata[i])**2)**0.5

        # get inter-sample times
        inttime = numpy.diff(timedata[i])

        # recalculate inter-sample times to seconds
        inttime = inttime / 1000
        
        # VELOCITY AND ACCELERATION
        # the velocity between samples is the inter-sample distance
        # divided by the inter-sample time
        vel = intdist / inttime

        # the acceleration is the sample-to-sample difference in
        # eye movement velocity
        acc = numpy.diff(vel)

        # SACCADE START AND END
        t0i = 0
        stop = False
        while not stop:
            # saccade start (t1) is when the velocity and acceleration
            # surpass threshold, saccade end (t2) is when both return
            # under threshold

            # detect saccade starts
            sacstarts = numpy.where((vel[1+t0i:] > minvel).astype(int) + (acc[t0i:] > minacc).astype(int) == 2)[0]
            if len(sacstarts) > 0:
                # timestamp for starting position
                t1i = t0i + sacstarts[0] + 1 #index of sacstart in xdata, ydata and timedata
                if t1i >= len(timedata[i])-1:
                    t1i = len(timedata[i])-2
                t1 = timedata[i][t1i]
                
                # add to saccade starts
                Ssac.append([t1])

                # detect saccade endings
                sacends = numpy.where((vel[1+t1i:] < minvel).astype(int) + (acc[t1i:] < minacc).astype(int) == 2)[0] 
                if len(sacends) > 0:
                    # timestamp for ending position
                    t2i = sacends[0] + t1i + 1
                    if t2i >= len(timedata[i]):
                        t2i = len(timedata[i])-1
                    t2 = timedata[i][t2i]
                    dur = t2 - t1

                    # ignore saccades that did not last long enough
                    if dur >= mindur:
                        #only store if there are no missings
                        if xdata[i][t1i] != missing and ydata[i][t1i] != missing and xdata[i][t2i] != missing and ydata[i][t2i] != missing:
                            # add to saccade ends
                            x1 = xdata[i][t1i]
                            y1 = ydata[i][t1i]
                            x2 = xdata[i][t2i]
                            y2 = ydata[i][t2i]
                            
                            # calculate distance from start to end
                            slen = (((x2-x1)**2) + ((y2-y1)**2))**0.5
                            
                            #if saccade lenght is one timestamp, do not calculate mean
                            if vel[t1i] == vel[t2i-1]:
                                svel= vel[t1i]
                            else:
                                svel = numpy.mean(vel[t1i:t2i-1])
                            
                            if acc[t1i-1] == acc[t2i-1] or acc[t1i-1] == acc[t2i-2]:
                                sacc = acc[t1i-1]
                            else:
                                sacc = numpy.max(acc[t1i-1:t2i-2])

                            # store starting time, ending time, 
                            # starting x and y coordinate, ending x and y coordinate,
                            # saccade lenght, velocity, acceleration)
                            Esac.append([t1, t2, dur, xdata[i][t1i], ydata[i][t1i], xdata[i][t2i], ydata[i][t2i], slen, svel, sacc])
                        else:
                            Ssac.pop(-1)
                    else:
                        # remove last saccade start on too low duration
                        Ssac.pop(-1)

                    # update t0i
                    t0i = 0 + t2i
                else:
                    stop = True
            else:
                stop = True
    
    return Ssac, Esac
