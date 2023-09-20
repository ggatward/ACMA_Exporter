#!/usr/bin/python3
# -*- coding: utf-8 -*-

from json.tool import main
import xml.etree.ElementTree as xml
import requests, sys, os, glob
import datetime, tempfile, yaml, csv

# pip install geopy
from geopy.distance import distance


# request properties
acmauri = 'https://api.acma.gov.au/SpectrumLicensingAPIOuterService/OuterService.svc'




def getUrl(url):
    # Get the URL and save the content to the tempfile
    resp = requests.get(url)
    with open('/tmp/xmlfile.xml', 'wb') as f:
        f.write(resp.content)


def parseXML(xmlfile):
    tree = xml.parse(xmlfile)
    root = tree.getroot()
    return root


def getLicences(clientId):
    licenceList = []
    xmlfile = getUrl(acmauri + '/LicenceSearchXML?searchText=' + clientId + '&ResultsLimit=1000')

    # Parse the XML
    root = parseXML('/tmp/xmlfile.xml')

    if root is None:
        logging.warn("Request for xml returned nothing, skipping")
        print('no xml')
        return

    for child in root:
        for sub in child:
            if (sub.tag == 'Licences'):
                for licences in sub:
                    # Extract the LICENCE_NO from each licence
                    addLic = True
                    for licenceData in licences:
                        if (licenceData.tag == 'LICENCE_NO'):
                            licenceNo = licenceData.text
                        if (licenceData.tag == 'LICENCE_CATEGORY'):
                            # Exclude Point to Point links from the list
                            if (licenceData.text == 'Fixed - Point to Point'):
                                addLic = False
                            if (licenceData.text == 'Radiodetermination - Radiodetermination'):
                                addLic = False

                    if (addLic):
                        # Append the licence number to our list
                        licenceList.append(licenceNo)

    # Return the list of licences
    return licenceList


def getSites(siteId):
    xmlfile = getUrl(acmauri + '/SiteSearchXML/' + siteId + '?searchField=SITE_ID')
    root = parseXML('/tmp/xmlfile.xml')

    for child in root:
        for sub in child:
            if (sub.tag == 'Sites'):
                for sites in sub:
                    for siteData in sites:
                        if (siteData.tag == 'CITY'):
                            city = siteData.text
                        if (siteData.tag == 'LATITUDE'):
                            lat = siteData.text
                        if (siteData.tag == 'LONGITUDE'):
                            lon = siteData.text
                        if (siteData.tag == 'LONG_NAME'):
                            name = siteData.text
    return(city,lat,lon,name)


def getRegistrations(licenceList,clientId,system):
    f = open('output/' + system + '_' + clientId + '.csv', 'w')
    # Write our CSV header
    f.write("frequency,location,lat,lon,mode\n")
    for licenceId in licenceList:
        xmlfile = getUrl(acmauri + '/RegistrationSearchXML?searchField=LICENCE_NO&searchText=' + licenceId)
        root = parseXML('/tmp/xmlfile.xml')

        for child in root:
            for sub in child:
                if (sub.tag == 'Registrations'):
                    for registrations in sub:
                        isTx = False
                        site = ''
                        city = ''
                        # Extract the FREQ and SITE_ID from each registration
                        for registrationData in registrations:
                            if (registrationData.tag == 'FREQ'):
                                freq = int(registrationData.text)/1000000
                            if (registrationData.tag == 'SITE_ID'):
                                site = registrationData.text
                            if (registrationData.tag == 'EMISSION_DESIG'):
                                mode = registrationData.text
                            if (registrationData.tag == 'DEVICE_TYPE_TEXT'):
                                # Only get Repeater/Base Transmit allocations
                                if (registrationData.text == 'Transmitter'):
                                    isTx = True
                        if (isTx):
                            if (site != ''):
                                (city,lat,lon,name) = getSites(site)
                            else:
                                city = "STATEWIDE"
                                lat = "0.0"
                                lon = "0.0"
                            print(str(freq) + ',' + city + ',' + lat + ',' + lon + ',' + mode)
                            csvstring = str(freq) + ',' + city + ',' + lat + ',' + lon + ',' + mode + '\n'
                            f.write(csvstring)
                            f.flush()
    f.close()


def combineCSV(system):
    fileList = glob.glob('output/' + system + '_*.csv')
    f = open('output/' + system + '.csv', 'w')
    # Add the new CSV header to the top
    f.write("frequency,location,lat,lon,mode\n")
    # Add each individual CSV to the system CSV
    for csvFile in fileList:
        with open(csvFile) as fp:
            data = fp.readlines()
            for line in data:
                if "lat" not in line:
                    f.write(line)
            fp.close()
    f.close()


def getPoints(system):
    # Read in data from CSV
    with open('output/' + system + '.csv', newline='') as csvfile:
        points = []
        data = csv.DictReader(csvfile)
        # Add all lat/lons to our points list
        for row in data:
            points.append([float(row['lat']),float(row['lon'])])
    return(points)


def groupSites(system,points,service_type):
    # Read in data from CSV
    f = open('output/' + system + '.hpd', 'w')
    with open('output/' + system + '.csv', newline='') as csvfile:
        data = csv.DictReader(csvfile)

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
            reader = csv.reader(open('output/' + system + '.csv', 'r'), delimiter=",")
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

        # Generate HPD outputs
        f.write('TargetModel\tBCDx36HP\r\n')
        f.write('FormatVersion\t1.00\r\n')
        f.write('Conventional\t\t\t' + system + '\tOff\t\tConventional\tOff\t0\t2\tOn\tOff\t400\tAuto\t8\r\n')
        f.write('DQKs_Status\t\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\tOn\r\n')

        groupId = 0
        for group in main_grouplist:
            if len(group) > 0:
                f.write('C-Group\tCGroupId=' + str(groupId) +'\tAgencyId=0\t' + group[0][1] + '\tOff\t' + group[0][2] + '\t' + group[0][3] + '\t50.0\tCircle\tNone\tGlobal\r\n')
                groupId += 1
                # Output the CHANNELS data for the SITE
                for line in group:
                    if float(line[0]) > 30:   # Remove any HF frequencies from the output
                        freq = int(float(line[0]) * 1000000)
                        avoid = 'Off'
                        # Set the mode based on the modulation
                        if line[4].strip() == '6K00A3E':
                            mode = 'AM'
                        else:
                            mode = 'NFM'
                        attenuator = 'Off'
                        delay = '2'
                        f.write('C-Freq\t\t\t' + line[1] + '\t' + avoid + '\t' + str(freq) + '\t' + mode + '\t\t' + service_type + '\t' + attenuator + '\t' + delay + '\t0\tOff\tAuto\tOff\tOn\tOff\tOff\r\n')
                        f.flush()
    f.close()


####################################

def cleanup(system):
    hpdFileList = glob.glob('output/*.hpd')
    csvFileList = glob.glob('output/' + system + '.csv')
    for filePath in hpdFileList:
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
    #   15 = Aviation

    clients = [
        { "clientID": "391222", "system": "Aviation", "service_type": "15" },
        { "clientID": "389917", "system": "Aviation", "service_type": "15" },
        #{ "clientID": "396261", "system": "Aviation", "service_type": "15" },
        #{ "clientID": "401054", "system": "Aviation", "service_type": "15" },
        #{ "clientID": "399343", "system": "Aviation", "service_type": "15" },
        { "clientID": "CUSTOM", "system": "Aviation", "service_type": "15" },
        #{ "clientID": "20011941", "system": "ASNSW" , "service_type": "1" },
        #{ "clientID": "17661", "system": "ASNSW2" },
        #{ "clientID": "37658", "system": "SJA" },
        #{ "clientID": "20012532", "system": "SES" },
        #{ "clientID": "516364", "system": "SES2" },
        #{ "clientID": "20005985", "system": "RFS" },
        #{ "clientID": "5832", "system": "RFS2" },
        #{ "clientID": "20027621", "system": "OEH" },
        #{ "clientID": "20012756", "system": "Commonwealth_Agencies" },
        #{ "clientID": "20019469", "system": "Low_Power" },
        #{ "clientID": "20008471", "system": "FRNSW" },
        #{ "clientID": "20020998", "system": "RMS" },
        #{ "clientID": "20036348", "system": "HGSA" },
        #{ "clientID": "115634", "system": "NPWS" },
        #{ "clientID": "20029221", "system": "QPRC" },
        #{ "clientID": "46975", "system": "DoD" },
    ]

    for item in clients:
        clientId = item["clientID"]
        system = item["system"]
        service_type = item["service_type"]
        print('Processing ' + clientId + ' - ' + system)
        # Clean any pre-exising output
        cleanup(system)

        if clientId != "CUSTOM":
            # Get all licences for the client
            clientLicences = getLicences(clientId)

            # Get Freq and Site for each licence (creates CSV per client-id)
            getRegistrations(clientLicences,clientId,system)

        # Combine all the CSVs from the same system
        combineCSV(system)

        # Group nearby sites together
        points=getPoints(system)
        groupSites(system,points,service_type)

        # Finally clean out any empty files in the output dir
        deleteEmptyFiles()
