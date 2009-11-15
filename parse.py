# -*- coding: utf-8 -*-

import re

# Frequently used regular expressions are pre-compiled
entryRe1 = re.compile(r'insertText\((\d+),(\d+),"(.*?)", (\d+), \'course\'\);', re.IGNORECASE)
lectureRe1 = re.compile(r'^(.*?) - (.*?), (.*?), \D*,* (.*?);<br>(.*?)$')

entryRe2 = re.compile(r'<td rowspan="(\d+)" id="c\d+" name="c(\d)(\d+)" class="classCell" align="center" bgcolor="(.*?)" valign="top"><h4>(.*?)</h4></td>', re.IGNORECASE)
lectureRe2 = re.compile(r'^(.*?) - (.*?), (.*?), \D*,* (.*?);<br>(.*?)$')
reservationRe1 = re.compile('^(.*?)<br>(.*?) (.*?) (.*?)<br>(.*?) (.*?) (.*?)$')
reservationRe2 = re.compile('^(.*?)<br>(.*?) (.*?) (.*?)$')

startDateRe = re.compile(r'<h2>Pon, (\d+).(\d+).(\d+)</h2>', re.IGNORECASE)
endDateRe = re.compile(r'<h2>Sob, (\d+).(\d+).(\d+)</h2>', re.IGNORECASE)

def parseHtml(data):
    startDate = re.findall(startDateRe, data)
    startDate = ('0' + startDate[0][0] if int(startDate[0][0]) < 10 else startDate[0][0]) + '.' + ('0' + startDate[0][1] if int(startDate[0][1]) < 10 else startDate[0][1]) + '.' + startDate[0][2] if len(startDate) > 0 else ''
    endDate = re.findall(endDateRe, data)
    endDate = ('0' + endDate[0][0] if int(endDate[0][0]) < 10 else endDate[0][0]) + '.' + ('0' + endDate[0][1] if int(endDate[0][1]) < 10 else endDate[0][1]) + '.' + endDate[0][2] if len(endDate) > 0 else ''
    matches = re.findall(entryRe1, data)
    
    # Loop over all the matches and parse the data
    result = {}
    days = [[], [], [], [], [], []]

    for match in matches:
        day = int(match[0])
        start = int(match[1])
        length = int(match[3])
        
        data = re.search(lectureRe1, match[2])
    
        if data != None:
            # Lecture
            lecture = data.group(1)
            professor = data.group(4)
            location = data.group(3)
    
        lectureData = [lecture, professor, location, start - 1, start + length - 1]
        days[day - 1].append(lectureData)
        
    result = dict([days.index(lecturesData) + 1, lecturesData] for lecturesData in days)

    return (startDate, endDate, result)
    
def parseGeneratedHtml(data):
    startDate = re.findall(startDateRe, data)
    startDate = startDate[0] if len(startDate) > 0 else ''
    endDate = re.findall(endDateRe, data)
    endDate = endDate[0] if len(endDate) > 0 else ''
    matches = re.findall(entryRe2, data)

    # Loop over all the matches and parse the data
    result = {}
    days = [[], [], [], [], [], []]
    
    for match in matches:
        day = int(match[1])
        start = int(match[2])
        length = int(match[0])
        type = match[3]
        
        if re.search(lectureRe2, match[4]) != None:
            # Lecture
            data = re.search(lectureRe2, match[4])
            
            lecture = data.group(1)
            professor = data.group(4)
            location = data.group(3);
        elif re.search(reservationRe1, match[4]) != None:
            # Reservation - 2 assistants
            data = re.search(reservationRe1, match[4])
            
            lecture = data.group(1)
            professor = data.group(4)
            location = data.group(3)
        elif re.search(reservationRe2, match[4]) != None:
            # Reservation - 1 assistant
            data = re.search(reservationRe2, match[4])
            
            lecture = data.group(1)
            professor = data.group(4)
            location = data.group(3)

        lectureData = [lecture, type, professor, location, start - 1, start + length - 1]
        days[day - 1].append(lectureData)
        
    result = dict([days.index(lecturesData) + 1, lecturesData] for lecturesData in days)
    
    return (startDate, endDate, result)