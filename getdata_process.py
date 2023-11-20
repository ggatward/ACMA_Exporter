#!/usr/bin/python3
# -*- coding: utf-8 -*-

from json.tool import main
from re import S
import xml.etree.ElementTree as xml
import requests, os, glob
# import sys
import datetime, tempfile, yaml, csv

# pip install geopy
from geopy.distance import distance


# request properties
acmauri = 'https://api.acma.gov.au/SpectrumLicensingAPIOuterService/OuterService.svc'


def combineCSV(favourite,system):
    fileList = glob.glob('downloads/' + favourite + '_' + system + '_*.csv')
    fileList.extend(glob.glob('input/' + favourite + '_' + system + '.csv'))
    outfile = 'output/' + favourite + '_' + system + '.csv'
    f = open(outfile, 'w')
    # Add the new CSV header to the top
    f.write("frequency,location,lat,lon,mode,alphatag\n")
    # Add each individual CSV to the system CSV
    for csvFile in fileList:
        with open(csvFile) as fp:
            data = fp.readlines()
            for line in data:
                if "lat" not in line:
                    f.write(line)
            fp.close()
    f.close()
    return outfile


def getPoints(finalCSV):
    # Read in data from CSV
    with open(finalCSV, newline='') as csvfile:
        points = []
        data = csv.DictReader(csvfile)
        # Add all lat/lons to our points list
        for row in data:
            points.append([float(row['lat']),float(row['lon'])])
    return(points)


####################################

def groupSites(csvFile,points,service_type,syskey,range):
    x1 = csvFile.split('/')
    x2 = x1[1].split('_')
    favourite = x2[0]
    x3 = x2[1].split('.')
    system = x3[0]

    fav1 = 'output/' + favourite + '.hpd'
    fav2 = 'output/' + favourite + '_nogps.hpd'

    # Create the top-level favourite files (only if they don't already exist)
    if os.path.exists(fav1):
        print('The file exists!')
    else:
        f1 = open(fav1, 'w' ,newline='')
        f1.write('TargetModel\tBCDx36HP\r\n')
        f1.write('FormatVersion\t1.00\r\n')
        f1.close()

    # Headers for nogps file
    if os.path.exists(fav2):
        print('The file exists!')
    else:
        f2 = open(fav2, 'w' ,newline='')
        f2.write('TargetModel\tBCDx36HP\r\n')
        f2.write('FormatVersion\t1.00\r\n')
        f2.close()

### Use a loop sequence rather than clientID here ????
    s1 = open('output/' + favourite + '_' + system + '_merged' + '.hpd', 'w' ,newline='')
    s2 = open('output/' + favourite + '_' + system + '_merged' + '_nogps.hpd', 'w' ,newline='')

    # Read in data from CSV
    sysdelay = '0'
    p25wait = '500'
    p25thresh = '6'
    p25threshmode = 'Manual'
    anaagc = 'On'
    p25agc = 'On'

    with open(csvFile, newline='') as csvInput:
        data = csv.DictReader(csvInput)

        main_grouplist_raw = []
        main_grouplist = []

        for row in data:
            points_filtered = []

            # Set input_point to first lat/lon
            input_point = (float(row['lat']),float(row['lon']))

            # add any locations in our csv within 'x' km to 'points_filtered'
            for point in points:
                if distance(input_point, point).km < 10:
                    points_filtered.append(point)

            # Loop through the csv again, and extract all the entries that are in our points_filtered list
            location_group = []
            res_list = []
            reader = csv.reader(open(csvFile, 'r'), delimiter=",")
            for line in reader:
                for fpoint in points_filtered:
                    if line[2] == str(fpoint[0]) and line[3] == str(fpoint[1]):
                        location_group.append(line)

            # Remove any duplicates from the resultant list
            for record in location_group:
                if record not in res_list:
                    res_list.append(record)

            # Add the resulting group to the main group list
            main_grouplist_raw.append(res_list)


        # Remove any duplicate site groupings
        for entry in main_grouplist_raw:
            if entry not in main_grouplist:
                main_grouplist.append(entry)

        # Check if the current system is the same as the previous loop - if not we need a new header.
        global lastSystem
        if lastSystem != system:
            # Generate HPD SYSTEM outputs
            s1.write('Conventional\t\t\t' + system + '\tOff\t\tConventional\t' + syskey + '\t0\t' + sysdelay + '\t' + anaagc + '\t' + p25agc + '\t' + p25wait + '\t' + p25threshmode + '\t' + p25thresh + '\r\n')
            s1.write('DQKs_Status\t\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\r\n')
            # Headers for nogps file
            s2.write('Conventional\t\t\t' + system + '\tOff\t\tConventional\t' + syskey + '\t0\t' + sysdelay + '\t' + anaagc + '\t' + p25agc + '\t' + p25wait + '\t' + p25threshmode + '\t' + p25thresh + '\r\n')
            s2.write('DQKs_Status\t\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\r\n')
        lastSystem = system

        groupId = 0
        for group in main_grouplist:
            if len(group) > 0:
                if (group[0][1] == 'STATEWIDE') or (group[0][1] == 'NATIONWIDE') or (group[0][2] == '0.0'):
                    s2.write('C-Group\tCGroupId=' + str(groupId) +'\tAgencyId=0\t' + group[0][1] + '\tOff\t' + group[0][2] + '\t' + group[0][3] + '\t' + range + '\tCircle\tNone\tGlobal\r\n')
                    groupId += 1
                    # Output the CHANNELS data for the SITE
                    for line in group:
                        if float(line[0]) > 148 and float(line[0]) < 150:  # Remove any Pager frequencies from the output
                            continue
                        if float(line[0]) < 30:   # Remove any HF frequencies from the output
                            continue
                        if float(line[0]) > 1300:  # Remove anything above
                            continue

                        freq = int(float(line[0]) * 1000000)
                        avoid = 'Off'
                        # Set the mode based on the modulation
                        if line[4].strip() == '6K00A3E':
                            mode = 'AM'
                            type = 'Analog'
                        else:
                            mode = 'NFM'
                            type = 'Auto'
                        if freq > 118000000 and freq < 137000000:
                            mode = 'AM'
                            type = 'Analog'
                        if line[5] == '':
                            alphatag = line[1]
                        else:
                            alphatag = line[5]
                        attenuator = 'Off'
                        delay = '2'
                        s2.write('C-Freq\t\t\t' + alphatag + '\t' + avoid + '\t' + str(freq) + '\t' + mode + '\t\t' + service_type + '\t' + attenuator + '\t' + delay + '\t0\tOff\tAuto\tOff\tOn\tOff\tOff\r\n')
                        s2.flush()
                else:
                    s1.write('C-Group\tCGroupId=' + str(groupId) +'\tAgencyId=0\t' + group[0][1] + '\tOff\t' + group[0][2] + '\t' + group[0][3] + '\t' + range + '\tCircle\tNone\tGlobal\r\n')
                    groupId += 1
                    # Output the CHANNELS data for the SITE
                    for line in group:
                        if float(line[0]) > 148 and float(line[0]) < 150:  # Remove any Pager frequencies from the output
                            continue
                        if float(line[0]) < 30:     # Remove any HF frequencies from the output
                            continue
                        if float(line[0]) > 1300:  # Remove anything above
                            continue

                        freq = int(float(line[0]) * 1000000)
                        avoid = 'Off'
                        # Set the mode based on the modulation
                        if line[4].strip() == '6K00A3E':
                            mode = 'AM'
                            type = 'Analog'
                        else:
                            mode = 'NFM'
                            type = 'Auto'
                        if freq > 118000000 and freq < 137000000:
                            mode = 'AM'
                            type = 'Analog'
                        if line[5] == '':
                            alphatag = line[1]
                        else:
                            alphatag = line[5]
                        attenuator = 'Off'
                        delay = '2'
                        s1.write('C-Freq\t\t\t' + alphatag + '\t' + avoid + '\t' + str(freq) + '\t' + mode + '\t\t' + service_type + '\t' + attenuator + '\t' + delay + '\t0\tOff\tAuto\tOff\tOn\tOff\tOff\r\n')
                        s1.flush()
    s1.close()
    s2.close()

####################################

def mergeFiles(favourite):
    print("Merging files for " + favourite)
    hpdFileList1 = glob.glob('output/' + favourite + '_*_merged_nogps.hpd')
    with open('output/' + favourite + '_nogps.hpd', 'a' ,newline='\r\n') as outfile:
        for fname1 in hpdFileList1:
            with open(fname1) as infile:
                outfile.write(infile.read())
            try:
                os.remove(fname1)
            except:
                print("Error while deleting file : ", fname1)

    hpdFileList2 = glob.glob('output/' + favourite + '_*_merged.hpd')
    with open('output/' + favourite + '.hpd', 'a' ,newline='\r\n') as outfile:
        for fname2 in hpdFileList2:
            with open(fname2) as infile:
                outfile.write(infile.read())
            try:
                os.remove(fname2)
            except:
                print("Error while deleting file : ", fname2)


####################################
def prerunClean(favourite):
    hpdFileList = glob.glob('output/' + favourite + '*.hpd')
    for filePath in hpdFileList:
        try:
            os.remove(filePath)
        except:
            print("Error while deleting file : ", filePath)


def cleanup(favourite,system,clientId):
    hpdFileList = glob.glob('output/' + favourite + '_' + system + '*.hpd')
    csvFileList = glob.glob('output/' + favourite + '_' + system + '_' + clientId + '.csv')
    for filePath in hpdFileList:
        try:
            os.remove(filePath)
        except:
            print("Error while deleting file : ", filePath)
    for filePath in csvFileList:
        try:
            os.remove(filePath)
        except:
            print("Error while deleting file : ", filePath)


def deleteEmptyFiles():
    str_directory = 'output/'
    # get list of all files in the directory and remove possible hidden files
    list_files = [x for x in os.listdir(str_directory) if x[0]!='.']
    # now loop through the files and remove empty ones
    for each_file in list_files:
        file_path = '%s/%s' % (str_directory, each_file)
        # check size and delete if 0
        if os.path.getsize(file_path)==0:
            os.remove(file_path)
        else:
            pass


if __name__ == "__main__":

    # 391222    Airservices Australia ACT/NSW Services
    # 389917    Airservices Australia VIC/TAS Services
    # 396261    Airservices Australia SA/NT Services
    # 401054    Airservices Australia QLD Services
    # 399343    Airservices Australia WA Services
    # 1441780   Airservices Australia RFF

    # 476492    QANTAS
    # 1412657   VIRGIN AUSTRALIA AIRLINES PTY LTD
    # 205799    VIRGIN AUSTRALIA REGIONAL AIRLINES PTY LTD
    # 85022     Sunstate Airlines (QLD) Pty. Limited
    # 91419     Eastern Australia Airlines Pty. Limited
    # 1142881   Alliance Airlines
    # 46945     Jetstar Airways Pty Ltd
    # 1313682   Regional Express
	# 1314310   Regional Express
    # 20053302  PELICAN AIRLINES PTY LTD
    # 1421512   Dnata Airport Services
    # 20003775  SWISSPORT

    # 20011941  NEW SOUTH WALES GOVERNMENT TELECOMMUNICATIONS AUTHORITY (NSW Ambulance)
    # 20005985  NEW SOUTH WALES GOVERNMENT TELECOMMUNICATIONS AUTHORITY (RFS)
    # 20012532  NEW SOUTH WALES GOVERNMENT TELECOMMUNICATIONS AUTHORITY (SES)
    # 20027621  NEW SOUTH WALES GOVERNMENT TELECOMMUNICATIONS AUTHORITY (OEH)
    # 20012756  NEW SOUTH WALES GOVERNMENT TELECOMMUNICATIONS AUTHORITY (Commonwealth Agencies)
    # 20019469  NEW SOUTH WALES GOVERNMENT TELECOMMUNICATIONS AUTHORITY (Low Power Services)
    # 20017375  NEW SOUTH WALES GOVERNMENT TELECOMMUNICATIONS AUTHORITY (Essential Energy)
    # 20008471  NEW SOUTH WALES GOVERNMENT TELECOMMUNICATIONS AUTHORITY (FRNSW)
    # 20020998  NEW SOUTH WALES GOVERNMENT TELECOMMUNICATIONS AUTHORITY (RMS)
    # 525851    NEW SOUTH WALES GOVERNMENT TELECOMMUNICATIONS AUTHORITY (GRN)
    # 20036348  NEW SOUTH WALES GOVERNMENT TELECOMMUNICATIONS AUTHORITY (HGSA)

    # 516364    SES
    # 1214220   Essential Energy
    # 17661     ASNSW
    # 115634    OFFICE OF ENVIRONMENT AND HERITAGE (NPWS)
    # 20029221  QPRC

    # Service Types:
    #    1 = Multi Dispatch
    #    3 = Fire Dispatch
    #    4 = EMS Dispatch
    #   15 = Aviation

    clients = [
        { "clientID": "391222", "favourite": "Aviation", "system": "Airservices", "service_type": "15", "syskey": "0", "range": "75" },
        { "clientID": "389917", "favourite": "Aviation", "system": "Airservices", "service_type": "15", "syskey": "0", "range": "75" },
        { "clientID": "396261", "favourite": "Aviation", "system": "Airservices", "service_type": "15", "syskey": "0", "range": "75"},
        { "clientID": "401054", "favourite": "Aviation", "system": "Airservices", "service_type": "15", "syskey": "0", "range": "75"},
        { "clientID": "399343", "favourite": "Aviation", "system": "Airservices", "service_type": "15", "syskey": "0", "range": "75" },
        { "clientID": "1441780", "favourite": "Aviation", "system": "Airservices RFF", "service_type": "15", "syskey": "3", "range": "30" },
        { "clientID": "CUSTOM", "favourite": "Aviation", "system": "CTAF", "service_type": "15", "syskey": "1", "range": "75" },
        { "clientID": "CUSTOM", "favourite": "Aviation", "system": "Company", "service_type": "15", "syskey": "2", "range": "75" },
        { "clientID": "CUSTOM", "favourite": "Aviation", "system": "Defence", "service_type": "15", "syskey": "0", "range": "75" },
        { "clientID": "476492", "favourite": "Aviation", "system": "Company", "service_type": "15", "syskey": "2", "range": "75" },
        { "clientID": "1412657", "favourite": "Aviation", "system": "Company", "service_type": "15", "syskey": "2", "range": "75" },
        { "clientID": "205799", "favourite": "Aviation", "system": "Company", "service_type": "15", "syskey": "2", "range": "75" },
        { "clientID": "85022", "favourite": "Aviation", "system": "Company", "service_type": "15", "syskey": "2", "range": "75" },
        { "clientID": "91419", "favourite": "Aviation", "system": "Company", "service_type": "15", "syskey": "2", "range": "75" },
        { "clientID": "1142881", "favourite": "Aviation", "system": "Company", "service_type": "15", "syskey": "2", "range": "75" },
        { "clientID": "46945", "favourite": "Aviation", "system": "Company", "service_type": "15", "syskey": "2", "range": "75" },
        { "clientID": "1313682", "favourite": "Aviation", "system": "Company", "service_type": "15", "syskey": "2", "range": "75" },
        { "clientID": "1314310", "favourite": "Aviation", "system": "Company", "service_type": "15", "syskey": "2", "range": "75" },
        { "clientID": "20053302", "favourite": "Aviation", "system": "Company", "service_type": "15", "syskey": "2", "range": "75" },
        { "clientID": "1421512", "favourite": "Aviation", "system": "Company", "service_type": "15", "syskey": "2", "range": "75" },
        { "clientID": "20003775", "favourite": "Aviation", "system": "Company", "service_type": "15", "syskey": "2", "range": "75" },
#        { "clientID": "20011941", "favourite": "Emerg Services", "system": "ASNSW", "service_type": "4", "syskey": "2", "range": "40" },
        #{ "clientID": "17661", "system": "ASNSW2" },
        #{ "clientID": "37658", "system": "SJA" },
#        { "clientID": "20012532", "favourite": "Emerg Services", "system": "SES", "service_type": "1", "syskey": "3", "range": "40" },
        #{ "clientID": "516364", "system": "SES2" },
#        { "clientID": "20005985", "favourite": "Emerg Services", "system": "RFS", "service_type": "3", "syskey": "1", "range": "40" },
        #{ "clientID": "5832", "system": "RFS2" },
        #{ "clientID": "20027621", "system": "OEH" },
        #{ "clientID": "20012756", "system": "Commonwealth_Agencies" },
        #{ "clientID": "20019469", "system": "Low_Power" },
#        { "clientID": "20008471", "favourite": "Emerg Services", "system": "FRNSW", "service_type": "3", "syskey": "0", "range": "40" },
        #{ "clientID": "20020998", "system": "RMS" },
        #{ "clientID": "20036348", "system": "HGSA" },
        #{ "clientID": "115634", "system": "NPWS" },
        #{ "clientID": "20029221", "system": "QPRC" },
#        { "clientID": "46975", "favourite": "Defence", "system": "DoD", "service_type": "3", "syskey": "0", "range": "40"},
    ]

    global lastSystem
    lastSystem = None
    global favouriteList
    favouriteList = []
    global csvList
    csvList = []

    for item in clients:
        favourite = item["favourite"]
        prerunClean(favourite)
        # Build a unique list of our favourites
        if favourite not in favouriteList:
            favouriteList.append(favourite)

    for item in clients:
        clientId = item["clientID"]
        favourite = item["favourite"]
        system = item["system"]
        service_type = item["service_type"]
        syskey = item["syskey"]
        range = item["range"]
        print('Processing ' + clientId + ' - ' + system)

        # Clean any pre-exising output
        cleanup(favourite,system,clientId)

        # Combine all the CSVs from the same system
        finalCSV = combineCSV(favourite,system)
        csvDataString = finalCSV + ',' + service_type + ',' + syskey + ',' + range
        if csvDataString not in csvList:
            csvList.append(csvDataString)

    # Run loop per-favourite
    for dataString in csvList:
        myData = dataString.split(',')
        csvFile = myData[0]
        service_type = myData[1]
        syskey = myData[2]
        range = myData[3]

        # Build our mega csv file
        fv1 = csvFile.split('/')[1]
        favourite = fv1.split('_')[0]
        system = fv1.split('_')[1].split('.')[0]
        print(system)
        # Merge all Aviation csv's into one
        if favourite == 'Aviation' and system != 'Airservices RFF':
            print(csvFile)
            with open('output/' + favourite + '_tmp.csv', 'a' ,newline='') as outfile:
                with open(csvFile) as infile:
                    outfile.write(infile.read())
            outfile.close()
            print("DEBUG: " + favourite)
            # Remove duplicate lines (i.e. CSV header)
            inFile = open('output/' + favourite + '_tmp.csv', 'r')
            writeFile = open('output/' + favourite + '_Aviation.csv', 'w')
            tmp = set()
            for txtLine in inFile:
                if txtLine not in tmp:
                    writeFile.write(txtLine)
                    tmp.add(txtLine)
            inFile.close()
            writeFile.close()

            # Group nearby sites together
            points=getPoints('output/' + favourite + '_Aviation.csv')
            groupSites('output/' + favourite + '_Aviation.csv',points,service_type,syskey,range)
            continue

        # Group nearby sites together
        points=getPoints(csvFile)
        groupSites(csvFile,points,service_type,syskey,range)

        # Clean out any empty files in the output dir
        # deleteEmptyFiles()

    for favourite in favouriteList:
        mergeFiles(favourite)
