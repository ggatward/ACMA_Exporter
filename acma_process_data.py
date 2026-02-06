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

def groupSites(csvFile,points,service_type,syskey,siteRange,systemType,colour,colourMode,tgids):
    x1 = csvFile.split('/')
    x2 = x1[1].split('_')
    favourite = x2[0]
    x3 = x2[1].split('.')
    system = x3[0]

    fav1 = 'output/' + favourite + '.hpd'

    # Create the top-level favourite files (only if they don't already exist)
    if not os.path.exists(fav1):
        f1 = open(fav1, 'w' ,newline='')
        f1.write('TargetModel\tBCDx36HP\r\n')
        f1.write('FormatVersion\t1.00\r\n')
        f1.close()

### Use a loop sequence rather than clientID here ????
    s1 = open('output/' + favourite + '_' + system + '_merged' + '.hpd', 'a' ,newline='')

    # Read in data from CSV
    sysdelay = '0'
    p25wait = '500'
    p25thresh = '6'
    p25threshmode = 'Manual'
    anaagc = 'On'
    p25agc = 'On'
    attenuator = 'Off'
    delay = '2'
    # Trunking defaults
    idsearch = 'Off'
    endcode = 'Analog'
    modulation = 'AUTO'
    bandplan = 'Standard'

# 6K00A3E = AM Voice
# 10K1F3E = FM Voice, 12.5 kHz bandwidth
# 11K0F3E = FM Voice, 12.5 kHz bandwidth
# 14K0F3E = FM Voice, 20 kHz bandwidth
# 16K0F3E = FM Voice, 25 kHz bandwidth

# 10K1F9W = P25 Voice+Data
# 8K10F1E = P25 Phase I C4FM Voice (12.5 kHz slot)
# 8K10F1W = P25 Phase II H-CPM Voice

# 7K60FXE = DMR Digital Voice (TDMA 2 slot)
# 4K00F1E = NXDN (6.25 kHz) Digital Voice
# 4K00F1W = Nexedge
# 8K30F1E = NXDN/IDAS (12.5 kHz) Digital Voice


    with open(csvFile, newline='') as csvInput:
        data = csv.DictReader(csvInput)

        main_grouplist_raw = []
        main_grouplist = []

        for row in data:
            points_filtered = []

            # Set input_point to first lat/lon
            input_point = (float(row['lat']),float(row['lon']))

            # add any locations in our csv within 'x' km to 'points_filtered'
            if (systemType == "CONV"):
                dist = 10
            if (systemType == "MOTO") or (systemType == "P25"):
                dist = 0.1
            for point in points:
                if distance(input_point, point).km < dist:
                    points_filtered.append(point)

            # Loop through the csv again, and extract all the entries that are in our points_filtered list
            location_group = []
            res_list = []
            reader = csv.reader(open(csvFile, 'r'), delimiter=",")
            for line in reader:
                for fpoint in points_filtered:
                    if str(line[2]) != 'lat' and float(line[2]) == float(fpoint[0]) and float(line[3]) == float(fpoint[1]):
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
        if lastSystem != system or lastSystem is None:
            # Generate HPD SYSTEM outputs
            if (systemType == "CONV"):
                s1.write('Conventional\t\t\t' + system + '\tOff\t\tConventional\t' + syskey + '\t0\t' + sysdelay + '\t' + anaagc + '\t' + p25agc + '\t' + p25wait + '\t' + p25threshmode + '\t' + p25thresh + '\r\n')
            if (systemType == "MOTO"):
                s1.write('Trunk\t\t\t' + system + '\tOff\t\tMotorola\t' + idsearch + '\tOff\tAuto\tIgnore\tSrch\t' + syskey + '\tNone\t' + sysdelay + '\t' + anaagc + '\t' + p25agc + '\t' + endcode + '\tOff\tOff\tOn\r\n')
            if (systemType == "P25"):
                s1.write('Trunk\t\t\t' + system + '\tOff\t\tP25Standard\t' + idsearch + '\tOff\tAuto\tIgnore\tSrch\t' + syskey + '\tNone\t' + sysdelay + '\t' + anaagc + '\t' + p25agc + '\t' + endcode + '\tOff\tOff\tOn\r\n')
            s1.write('DQKs_Status\t\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\r\n')

        lastSystem = system

        groupId = 0
        siteId = 0
        for group in main_grouplist:
            if len(group) > 0:
                groupId += 1
                if (group[0][1] == 'NATIONWIDE'):
                    range = '4500'
                elif (group[0][1] == 'NSW-WIDE'):
                    range = '450'
                elif (group[0][1] == 'VIC-WIDE'):
                    range = '200'
                elif (group[0][1] == 'QLD-WIDE'):
                    range = '750'
                elif (group[0][1] == 'SA-WIDE'):
                    range = '500'
                elif (group[0][1] == 'WA-WIDE'):
                    range = '825'
                elif (group[0][1] == 'NT-WIDE'):
                    range = '560'
                elif (group[0][1] == 'TAS-WIDE'):
                    range = '190'
                else:
                    range = siteRange

                if (systemType == "CONV"):
                    s1.write('C-Group\tCGroupId=' + str(groupId) +'\tAgencyId=0\t' + group[0][1] + '\tOff\t' + group[0][2] + '\t' + group[0][3] + '\t' + range + '\tCircle\tNone\tGlobal\r\n')
                if (systemType == "MOTO") or (systemType == "P25"):
                    s1.write('Site\tSiteId=' + str(groupId) +'\tTrunkId=1\t' + group[0][1] + '\tOff\t' + group[0][2] + '\t' + group[0][3] + '\t' + range + '\t' + modulation + '\t' + bandplan + '\tWide\tCircle\tOff\t' + p25wait + '\t' + p25threshmode + '\t' + p25thresh + '\t' + str(siteId) + '\tOff\tGlobal\r\n')

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
                    try:
                        if line[5] == '':
                            alphatag = line[1]
                        else:
                            alphatag = line[5]
                    except:
                        alphatag = line[1]

                    if (systemType == "CONV"):
                        s1.write('C-Freq\t\t\t' + alphatag + '\t' + avoid + '\t' + str(freq) + '\t' + mode + '\t\t' + service_type + '\t' + attenuator + '\t' + delay + '\t0\tOff\tAuto\t' + colour + '\t' + colourMode + '\tOff\tOff\r\n')
                        s1.flush()
                    if (systemType == "MOTO") or (systemType == "P25"):
                        s1.write('T-Freq\tTFreqId=0\tSiteId=' + str(groupId) + '\t\t' + avoid + '\t' + str(freq) + '\t\tSrch\r\n')
                        s1.flush()

        # Add trunk data if relevant
        if tgids != 'None':
            print("Add TG IDs to system")
            try:
                with open('input/' + tgids) as tgfile:
                    s1.write(tgfile.read())
            except:
                print('Cannot open input/' + tgids)
    s1.close()

####################################

def mergeFiles(favourite):
    print("Building final favourite file for " + favourite)
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
    csvFileList = glob.glob('output/' + favourite + '*.csv')
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


def postrunCleanup(favourite):
    hpdFileList = glob.glob('output/' + favourite + '*_merged.hpd')
    csvFileList = glob.glob('output/' + favourite + '*.csv')
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


# def deleteEmptyFiles():
#     str_directory = 'output/'
#     # get list of all files in the directory and remove possible hidden files
#     list_files = [x for x in os.listdir(str_directory) if x[0]!='.']
#     # now loop through the files and remove empty ones
#     for each_file in list_files:
#         file_path = '%s/%s' % (str_directory, each_file)
#         # check size and delete if 0
#         if os.path.getsize(file_path)==0:
#             os.remove(file_path)
#         else:
#             pass


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
    # 525851    NEW SOUTH WALES GOVERNMENT TELECOMMUNICATIONS AUTHORITY (PSN)
    # 20036348  NEW SOUTH WALES GOVERNMENT TELECOMMUNICATIONS AUTHORITY (HGSA-PSN)
    # 160       ACT Emergency Services Agency (TRN)

    # 516364    SES
    # 1214220   Essential Energy
    # 17661     ASNSW
    # 115634    OFFICE OF ENVIRONMENT AND HERITAGE (NPWS)
    # 20029221  QPRC

    # 20011154  DEPARTMENT OF JUSTICE AND COMMUNITY SAFETY  (VICRMR)
	# 1315913   DEPARTMENT OF JUSTICE AND COMMUNITY SAFETY  (VICMMR)

    # Service Types:
    #    1 = Multi Dispatch
    #    3 = Fire Dispatch
    #    4 = EMS Dispatch
    #    8 = Fire-Tac
    #    9 = EMS-Tac
    #   11 = Interop
    #   12 = Hospital
    #   15 = Aviation
    #   20 = Railroad
    #   21 = Other
    #   24 = Fire-Talk
    #   25 = EMS-Talk
    #   26 = Transportation
    #   29 = Emergency Ops
    #   30 = Military
    #   34 = Utilities
    #  208 = Custom1

    # Colours: Off, Blue, Red, Magenta, Green, Cyan, Yellow, White
    # Colour Modes: On, Slow Blink, Fast Blink


    clients = [
        # { "clientID": "391222", "favourite": "Aviation", "system": "Airservices", "service_type": "15", "syskey": "0", "range": "75", "widetag": "NATIONAL", "system_type": "CONV" },
        # { "clientID": "389917", "favourite": "Aviation", "system": "Airservices", "service_type": "15", "syskey": "0", "range": "75", "widetag": "NATIONAL", "system_type": "CONV" },
        # { "clientID": "396261", "favourite": "Aviation", "system": "Airservices", "service_type": "15", "syskey": "0", "range": "75", "widetag": "NATIONAL", "system_type": "CONV" },
        # { "clientID": "401054", "favourite": "Aviation", "system": "Airservices", "service_type": "15", "syskey": "0", "range": "75", "widetag": "NATIONAL", "system_type": "CONV" },
        # { "clientID": "399343", "favourite": "Aviation", "system": "Airservices", "service_type": "15", "syskey": "0", "range": "75", "widetag": "NATIONAL", "system_type": "CONV" },
        # { "clientID": "CUSTOM", "favourite": "Aviation", "system": "Defence", "service_type": "15", "syskey": "0", "range": "75", "widetag": "NATIONAL", "system_type": "CONV" },
        # { "clientID": "CUSTOM", "favourite": "Aviation", "system": "CTAF", "service_type": "15", "syskey": "1", "range": "75", "widetag": "NATIONAL", "system_type": "CONV" },
        # { "clientID": "CUSTOM", "favourite": "Aviation", "system": "Company", "service_type": "15", "syskey": "2", "range": "75", "widetag": "NATIONAL", "system_type": "CONV" },
        # { "clientID": "476492", "favourite": "Aviation", "system": "Company", "service_type": "15", "syskey": "2", "range": "75", "widetag": "NATIONAL", "system_type": "CONV" },
        # { "clientID": "1412657", "favourite": "Aviation", "system": "Company", "service_type": "15", "syskey": "2", "range": "75", "widetag": "NATIONAL", "system_type": "CONV" },
        # { "clientID": "205799", "favourite": "Aviation", "system": "Company", "service_type": "15", "syskey": "2", "range": "75", "widetag": "NATIONAL", "system_type": "CONV" },
        # { "clientID": "1142881", "favourite": "Aviation", "system": "Company", "service_type": "15", "syskey": "2", "range": "75", "widetag": "NATIONAL", "system_type": "CONV" },
        # { "clientID": "46945", "favourite": "Aviation", "system": "Company", "service_type": "15", "syskey": "2", "range": "75", "widetag": "NATIONAL", "system_type": "CONV" },
        # { "clientID": "1313682", "favourite": "Aviation", "system": "Company", "service_type": "15", "syskey": "2", "range": "75", "widetag": "NATIONAL", "system_type": "CONV" },
        # { "clientID": "1314310", "favourite": "Aviation", "system": "Company", "service_type": "15", "syskey": "2", "range": "75", "widetag": "NATIONAL", "system_type": "CONV" },
        # { "clientID": "20053302", "favourite": "Aviation", "system": "Company", "service_type": "15", "syskey": "2", "range": "75", "widetag": "NATIONAL", "system_type": "CONV" },
        # { "clientID": "1421512", "favourite": "Aviation", "system": "Company", "service_type": "15", "syskey": "2", "range": "75", "widetag": "NATIONAL", "system_type": "CONV" },
        # { "clientID": "20003775", "favourite": "Aviation", "system": "Company", "service_type": "15", "syskey": "2", "range": "75", "widetag": "NATIONAL", "system_type": "CONV" },
        # { "clientID": "1441780", "favourite": "Aviation", "system": "Airservices RFF", "service_type": "15", "syskey": "3", "range": "30", "widetag": "NATIONAL", "system_type": "CONV" },
        #
        # National Marine
        # { "clientID": "CUSTOM", "favourite": "Marine", "system": "Marine", "service_type": "21", "syskey": "0", "range": "25", "widetag": "NATIONAL", "system_type": "CONV" },
        #
        # National Rail
        # { "clientID": "165570", "favourite": "Rail", "system": "ARTC", "service_type": "20", "syskey": "0", "range": "25", "widetag": "NATIONAL", "system_type": "CONV" },
        # { "clientID": "20033195", "favourite": "Rail", "system": "Pacific National", "service_type": "20", "syskey": "1", "range": "25", "widetag": "NATIONAL", "system_type": "CONV" },
        # { "clientID": "1504613", "favourite": "Rail", "system": "One Rail", "service_type": "20", "syskey": "2", "range": "25", "widetag": "NATIONAL", "system_type": "CONV" },
        # { "clientID": "1206023", "favourite": "Rail", "system": "GSR", "service_type": "20", "syskey": "3", "range": "25", "widetag": "NATIONAL", "system_type": "CONV" },
        #
        # National Defence - Exceeds 2000 entries
        # { "clientID": "46975", "favourite": "Defence", "system": "Defence", "service_type": "30", "syskey": "0", "range": "25", "widetag": "NATIONAL", "system_type": "CONV" },

        ########################
        # { "clientID": "160", "favourite": "NSW PSN", "system": "NSW PSN", "service_type": "21", "syskey": "0", "range": "25", "widetag": "NSW", "system_type": "P25" },
        # { "clientID": "525851", "favourite": "NSW PSN", "system": "NSW PSN", "service_type": "21", "syskey": "0", "range": "25", "widetag": "NSW", "system_type": "P25" },
        # { "clientID": "20036348", "favourite": "NSW PSN", "system": "NSW PSN", "service_type": "21", "syskey": "0", "range": "25", "widetag": "NSW", "system_type": "P25" },

        { "clientID": "20008471", "favourite": "NSW EMS", "system": "FRNSW", "service_type": "3", "syskey": "0", "range": "25", "widetag": "NSW", "system_type": "CONV" },
        { "clientID": "20005985", "favourite": "NSW EMS", "system": "RFS", "service_type": "3", "syskey": "1", "range": "25", "widetag": "NSW", "system_type": "CONV" },
        { "clientID": "CUSTOM", "favourite": "NSW EMS", "system": "RFS FG", "service_type": "8", "syskey": "2", "range": "25", "widetag": "NSW", "system_type": "CONV", "colour": "Red" },
        { "clientID": "20011941", "favourite": "NSW EMS", "system": "ASNSW", "service_type": "4", "syskey": "3", "range": "25", "widetag": "NSW", "system_type": "CONV" },
        { "clientID": "20012532", "favourite": "NSW EMS", "system": "SES", "service_type": "1", "syskey": "4", "range": "25", "widetag": "NSW", "system_type": "CONV" },

        { "clientID": "115634", "favourite": "NSW MISC", "system": "NPWS", "service_type": "208", "syskey": "0", "range": "25", "widetag": "NSW", "system_type": "CONV" },
        { "clientID": "45451", "favourite": "NSW Rail", "system": "ZigZag", "service_type": "20", "syskey": "0", "range": "25", "widetag": "NSW", "system_type": "CONV" },
        #
        ########################
        # { "clientID": "84379", "favourite": "QLD EMS", "system": "QFES", "service_type": "3", "syskey": "0", "range": "25", "widetag": "QLD", "system_type": "CONV" },
        # { "clientID": "270141", "favourite": "QLD EMS", "system": "RFS", "service_type": "1", "syskey": "1", "range": "25", "widetag": "QLD", "system_type": "CONV" },
        # { "clientID": "79601", "favourite": "QLD EMS", "system": "QAS", "service_type": "4", "syskey": "3", "range": "25", "widetag": "QLD", "system_type": "CONV" },
        # { "clientID": "521072", "favourite": "QLD EMS", "system": "QAS", "service_type": "4", "syskey": "3", "range": "25", "widetag": "QLD", "system_type": "CONV" },
        # { "clientID": "1401916", "favourite": "QLD EMS", "system": "QAS", "service_type": "4", "syskey": "3", "range": "25", "widetag": "QLD", "system_type": "CONV" },
        # { "clientID": "20060946", "favourite": "QLD EMS", "system": "SES", "service_type": "4", "syskey": "4", "range": "25", "widetag": "QLD", "system_type": "CONV" },
        # { "clientID": "58050", "favourite": "QLD EMS", "system": "QPS", "service_type": "2", "syskey": "5", "range": "25", "widetag": "QLD", "system_type": "CONV" },

        # { "clientID": "1149151", "favourite": "QLD Rail", "system": "Queensland Rail", "service_type": "20", "syskey": "0", "range": "25", "widetag": "QLD", "system_type": "CONV" },
        # { "clientID": "20028378", "favourite": "QLD Rail", "system": "Queensland Rail", "service_type": "20", "syskey": "0", "range": "25", "widetag": "QLD", "system_type": "CONV" },
        # { "clientID": "20036656", "favourite": "QLD Rail", "system": "Queensland Rail", "service_type": "20", "syskey": "0", "range": "25", "widetag": "QLD", "system_type": "CONV" },
        # { "clientID": "20037246", "favourite": "QLD Rail", "system": "Queensland Rail", "service_type": "20", "syskey": "0", "range": "25", "widetag": "QLD", "system_type": "CONV" },


        ########################
        # { "clientID": "20011154", "favourite": "VIC xMR", "system": "VIC RMR", "service_type": "21", "syskey": "0", "range": "25", "widetag": "VIC", "system_type": "P25" },
        # { "clientID": "1315913", "favourite": "VIC xMR", "system": "VIC MMR", "service_type": "21", "syskey": "1", "range": "25", "widetag": "VIC", "system_type": "P25" },

        # { "clientID": "144590", "favourite": "VIC EMS", "system": "FRVIC", "service_type": "3", "syskey": "0", "range": "25", "widetag": "VIC", "system_type": "CONV" },
        # { "clientID": "210019", "favourite": "VIC EMS", "system": "CFA", "service_type": "3", "syskey": "1", "range": "25", "widetag": "VIC", "system_type": "CONV" },
        # { "clientID": "446656", "favourite": "VIC EMS", "system": "CFA", "service_type": "3", "syskey": "1", "range": "25", "widetag": "VIC", "system_type": "CONV" },
        # { "clientID": "159075", "favourite": "VIC EMS", "system": "AMBVIC", "service_type": "4", "syskey": "3", "range": "25", "widetag": "VIC", "system_type": "CONV" },
        # { "clientID": "159095", "favourite": "VIC EMS", "system": "SES", "service_type": "1", "syskey": "4", "range": "25", "widetag": "VIC", "system_type": "CONV" },

        # { "clientID": "1310687", "favourite": "VIC Rail", "system": "VicRail", "service_type": "20", "syskey": "0", "range": "25", "widetag": "VIC", "system_type": "CONV" },
        # { "clientID": "1141005", "favourite": "VIC Rail", "system": "VicRail", "service_type": "20", "syskey": "0", "range": "25", "widetag": "VIC", "system_type": "CONV" },
        # { "clientID": "20041674", "favourite": "VIC Rail", "system": "Puffing Billy", "service_type": "20", "syskey": "1", "range": "25", "widetag": "VIC", "system_type": "CONV" },


        ########################
        # { "clientID": "169283", "favourite": "SA EMS", "system": "CFS", "service_type": "3", "syskey": "1", "range": "25", "widetag": "SA", "system_type": "CONV" },

        # { "clientID": "1500993", "favourite": "SA Rail", "system": "Pichi Richi", "service_type": "20", "syskey": "0", "range": "25", "widetag": "SA", "system_type": "CONV" },


        ########################
        # { "clientID": "192835", "favourite": "WA EMS", "system": "DFESWA", "service_type": "3", "syskey": "1", "range": "25", "widetag": "WA", "system_type": "CONV" },
        # { "clientID": "206335", "favourite": "WA EMS", "system": "DFESWA", "service_type": "3", "syskey": "1", "range": "25", "widetag": "WA", "system_type": "CONV" },

        # { "clientID": "1147725", "favourite": "WA Rail", "system": "Hotham Valley", "service_type": "20", "syskey": "0", "range": "25", "widetag": "WA", "system_type": "CONV" },

        ########################
        # { "clientID": "180004", "favourite": "NT EMS", "system": "NTPOL", "service_type": "2", "syskey": "5", "range": "25", "widetag": "NT", "system_type": "CONV" },
    ]

    global lastSystem
    lastSystem = None
    global favouriteList
    favouriteList = []
    global csvList
    csvList = []
    global isAviation
    isAviation = False

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
        systemType = item["system_type"]
        try:
            colour = item["colour"]
        except:
            colour = 'Off'
        try:
            colourMode = item["colourMode"]
        except:
            colourMode = 'On'
        try:
            tgids = item["tgids"]
        except:
            tgids = 'None'

        print('Processing ' + clientId + ' - ' + system)

        # Combine all the CSVs from the same system
        finalCSV = combineCSV(favourite,system)
        csvDataString = finalCSV + ',' + service_type + ',' + syskey + ',' + range + ',' + systemType + ',' + colour + ',' + colourMode + ',' + tgids
        if csvDataString not in csvList:
            csvList.append(csvDataString)

    # Run loop per-favourite
    for dataString in csvList:
        myData = dataString.split(',')
        csvFile = myData[0]
        service_type = myData[1]
        syskey = myData[2]
        range = myData[3]
        systemType = myData[4]
        colour = myData[5]
        colourMode = myData[6]
        tgids = myData[7]

        # Build our mega csv file
        fv1 = csvFile.split('/')[1]
        favourite = fv1.split('_')[0]
        system = fv1.split('_')[1].split('.')[0]
        print("Merging sites for "+favourite+" - "+system)
        if favourite == 'Aviation':
            isAviation = True
        else:
            isAviation = False

        # Merge all Aviation csv's into one
        if favourite == 'Aviation' and system != 'Airservices RFF':
            print(csvFile)
            with open('output/' + favourite + '_tmp.csv', 'a' ,newline='') as outfile:
                with open(csvFile) as infile:
                    outfile.write(infile.read())
            outfile.close()
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
        if favourite == 'Aviation' and system != 'Airservices RFF':
            pass
        else:
            points=getPoints(csvFile)
            groupSites(csvFile,points,service_type,syskey,range,systemType,colour,colourMode,tgids)

    # Processing for Aviation lists
    if isAviation == True:
        print("Processing Aviation Data")
        points=getPoints('output/Aviation_Aviation.csv')
        groupSites('output/Aviation_Aviation.csv',points,'15','0','75','CONV',colour,colourMode,tgids)


    for favourite in favouriteList:
        mergeFiles(favourite)

    # Append TGID files to trunk hpd's
#    print("Appending NSW PSN TGIDs")

    # Clean any leftover processing output
    for favourite in favouriteList:
        postrunCleanup(favourite)
    # Final Aviation cleanup
    postrunCleanup('Aviation')
