# -*- coding: utf-8 -*-
#
# Name: Timetable Parser
# Description: Application for parsing FERI Timetable (http://www.feri.uni-mb.si/urniki/groups.asp) and exporting the data as txt, pdf or iCal.
# Author: Tomaž Muraus (http://www.tomaz-muraus.info)
# Version: 1.0
# License: GPL
#
# Requirements:
# - Windows / Linux / Mac
# - Python >= 2.6 (< 3.0)
# - Python cURL interface - pycURL (http://pycurl.sourceforge.net/)
# - Reportlab PDF library - reportlab (http://www.reportlab.org/oss/rl-toolkit/download/)
# - Python iCalendar library - VObject (http://vobject.skyhouseconsulting.com/)

import json
import StringIO
import re
import json
import sys
import datetime
import codecs

import pycurl
import vobject

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import *
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.lib import pagesizes
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import cm

import parse

# URLs
timetableUrl = 'http://www.feri.uni-mb.si/urniki/groups.asp'
branchesUrl = 'http://www.feri.uni-mb.si/urniki/lib/helper.asp?type=year&program_id=%s&year=%s'
groupsUrl = 'http://www.feri.uni-mb.si/urniki/lib/helper.asp?type=branch&branch_id=%s'

days = ['Ponedeljek', 'Torek', 'Sreda', 'Cetrtek', 'Petek', 'Sobota']
hours = sum([[('0' + str(i) if i < 10 else str(i)) + ":00", ('0' + str(i) if i < 10 else str(i)) + ":30"] for i in range(7, 21)], [])

def getPrograms():
    response = StringIO.StringIO()
    
    try:
        curl = pycurl.Curl()
        curl.setopt(pycurl.URL, timetableUrl)
        curl.setopt(pycurl.WRITEFUNCTION, response.write)
        curl.perform()
        curl.close()
        
        response = response.getvalue()
        
        if response != '':
            programs = re.findall(r'<option value="(.*?)">(.*?)</option>', response)
            
            returnString = ''
            if programs != None and len(programs) > 0:
                
                returnString += 'Programs:\n\n'
                for program in programs:
                    returnString += '%s - %s\n'  % (program[0], program[1])
                    
                return returnString
            else:
                raise Exception('Invalid response')
        else:
            raise Exception('Empty response')  
    except:
        return False

def getBranches(programId, year):
    response = StringIO.StringIO()
                                 
    try:
        url = branchesUrl % (programId, year)
        
        curl = pycurl.Curl()
        curl.setopt(pycurl.URL, url)
        curl.setopt(pycurl.WRITEFUNCTION, response.write)
        curl.perform()
        curl.close()
        
        response = response.getvalue()
        
        if response != '':
            response = json.loads(response)

            returnString = ''
            if 'result' in response and len(response['result'][1]) >= 1:

                returnString += 'Branches:\n\n'
                for branch in response['result'][1]:
                    returnString += '%s - %s\n'  % (branch['branch_id'], branch['name'])
                    
                return returnString
            else:
                raise Exception('Invalid response')
        else:
            raise Exception('Empty response')  
    except:
        return False
        
def getGroups(branchId): 
    response = StringIO.StringIO()
    
    try: 
        url = groupsUrl % (branchId)
        
        curl = pycurl.Curl()
        curl.setopt(pycurl.URL, url)
        curl.setopt(pycurl.WRITEFUNCTION, response.write)
        curl.perform()
        curl.close()
        
        response = json.loads(response.getvalue())
        
        if 'groups' in response: 
            i = 1
            groups = []
            for group in response['groups']:
                groups.append([i, group['groups_id']])
                i += 1
    except:
       return False
                 
    return groups

def getTimetable(date, programId, year, branchId):   
    response = StringIO.StringIO()
    groups = getGroups(branchId)
    
    if groups == False or len(groups) == 0:
        return False

    try:
        groupIndices = ',' . join('%s' % (group[0]) for group in groups)
        groupValues = ',' . join('%s' % (group[1]) for group in groups)
        
        curl = pycurl.Curl()
        curl.setopt(pycurl.URL, timetableUrl)
        curl.setopt(pycurl.POSTFIELDS, 'date_field=%s&program_index=%s&year_index=%s&branch_id=%s&with_groups=1&groups_index=%s&groups_values=%s' % (date, programId, year, branchId, groupIndices, groupValues))
        curl.setopt(pycurl.WRITEFUNCTION, response.write)
        curl.perform()
        curl.close()
        
        response = response.getvalue()
        
        if response != '':
            return response
        else:
            raise Exception('Empty response')  
    except:
        return False

def generateTimetable(format, date, programId, year, branchId):
    timetable = getTimetable(date, programId, year, branchId)
    
    if timetable != False:
        (startDate, endDate, data) = parse.parseHtml(timetable)

    if format == 'txt':
        fileName = generateTxt(startDate, endDate, data)
    elif format == 'pdf':
        fileName = generatePdf(startDate, endDate, data)
    elif format == 'ical':
        fileName = generateIcal(startDate, endDate, data)
            
    return fileName

def generateTxt(startDate, endDate, data):
    fileName = 'timetable_%s-%s.txt' % (startDate, endDate)
    
    with open(fileName, 'w') as file:
        for key in data:
            
            if len(data[key]) > 0:
                line = '%s: ' % (days[key - 1])
                line += ', ' . join('%s (%s) - %s - %s - %s' % (lecture[0], lecture[1], lecture[2], hours[lecture[3]], hours[lecture[4]]) for lecture in data[key])
                line += '\n'
                
                file.write(line)
                
    return fileName

def generatePdf(startDate, endDate, data):
    fileName = 'timetable_%s-%s.pdf' % (startDate, endDate)
    
    vera = TTFont("Vera", "Vera.ttf")
    pdfmetrics.registerFont(vera)
    
    PAGESIZE = pagesizes.landscape(pagesizes.A4)
    doc = SimpleDocTemplate(fileName, pagesize = PAGESIZE)
    
    styles = getSampleStyleSheet()
    style = ParagraphStyle('style')
    style.fontName = 'Vera'
    style.fontSize = 15;
    style.alignment = 1
    
    elements = []
    elements.append(Paragraph("Urnik <i>%s - %s</i>" % (startDate, endDate), style))
    elements.append(Spacer(0, 20))
    
    header = ['Ura', 'Ponedeljek', 'Torek', 'Sreda', 'Četrtek', 'Petek']
    
    tableData = []
    tableData.append(header)
    
    for i in range(1, len(hours)):
        
        data1 = [hours[i]]
        for j in range(1, len(data)):
            hour = i
            match = [lecture for lecture in data[j] if lecture[3] <= hour <= lecture[4] - 1]
    
            # Found a lecture which is on schedule this hour
            if len(match) == 1:
                data1.append(unicode(match[0][0] + '\n' + match[0][1] + '\n' + match[0][2], 'utf-8', 'ignore'))
            else:
                data1.append('')
                
        tableData.append(data1)
    
    table = Table(tableData)
    table.setStyle(TableStyle([
                               ('TOPPADDING', (0, 0), (-1, -1), 1),
                               ('SPAN', (0, 0), (1, 1)),
                               ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                               ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
                               ('INNERGRID', (0, 0), (-1, -1), 0.2, colors.black),
                               ('BOX', (0, 0), (-1, -1), 0.2, colors.black)
                               ]))
    
    elements.append(table)
    doc.build(elements)
    
    return fileName
    
def generateIcal(startDate, endDate, data):
    fileName = 'timetable_%s-%s.ics' % (startDate, endDate)
    startDate = datetime.date(int(startDate[6:]), int(startDate[3:5]), int(startDate[:2]))
      
    cal = vobject.iCalendar()
    for key in data:
        if len(data[key]) > 0:
                
            for lecture in data[key]:
                delta = datetime.timedelta(days = key - 1)
                date = startDate + delta

                event = cal.add('vevent')
                event.add('summary').value = '%s (%s)' % (unicode(lecture[0], 'utf-8', 'ignore'), unicode(lecture[1], 'utf-8', 'ignore'))
                event.add('location').value = 'FERI - %s' % (lecture[2])
                event.add('dtstart').value = datetime.datetime(date.year, date.month, date.day, int(hours[lecture[3]][:2]), int(hours[lecture[3]][3:]), 0, tzinfo = vobject.icalendar.utc)
                event.add('dtend').value = datetime.datetime(date.year, date.month, date.day, int(hours[lecture[4]][:2]), int(hours[lecture[4]][3:]), tzinfo = vobject.icalendar.utc)
    
    icalstream = cal.serialize()

    with codecs.open(fileName, 'w', 'ascii') as file:
        file.write(icalstream)
                
    return fileName

if __name__ == '__main__':
    argLen = len(sys.argv)
    
    if argLen > 1 and sys.argv[1] != '--help':
        if sys.argv[1] == '--programs':
            result = getPrograms()
            
            if result != False:
                print result
            else:
                print 'Failed'
            
        elif sys.argv[1] == '--branches' and argLen == 4:
            programId = sys.argv[2]
            year = sys.argv[3]

            result = getBranches(programId, year)
                
            if result != False:
                print result
            else:
                print 'Failed'
            
        elif sys.argv[1] == '--timetable' and argLen == 7:
            format = sys.argv[2]
            date = sys.argv[3]
            programId = sys.argv[4]
            year = sys.argv[5]
            branchId = sys.argv[6]
            
            result = generateTimetable(format, date, programId, year, branchId)
            
            if result != False:
                print 'Timetable saved as %s' % (result)
            else:
                print 'Failed'
            
        else:
            print 'Invalid option or number of arguments (use --help)'
    else:
        print 'Usage: python timetable_parser.py [OPTIONS]\n'
        print 'Options:'
        print '--programs -> lists available programs'
        print '--branches <program_id> <year> -> lists available branches for specified year and program'
        print '--timetable <txt|pdf|ical> <date> <program_id> <year> <branch_id> -> generates and saves a timetable in specified format for specified year, program and branch'
        sys.exit(0)