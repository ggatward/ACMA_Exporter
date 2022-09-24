#!/usr/bin/python3
# -*- coding: utf-8 -*-

import xml.etree.ElementTree as xml
import requests, sys, os, glob
import datetime, tempfile, yaml, csv

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
    xmlfile = getUrl(acmauri + '/LicenceSearchXML?searchText=' + clientId + '&ResultsLimit=2000')

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
    xmlfile = getUrl(acmauri + '/SiteSearchXML/' + siteId + '?searchField=SITE_ID&ResultsLimit=1000')
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


def getRegistrations(licenceList,clientId):
    f = open('output/' + clientId + '.csv', 'w')
    # Write our CSV header
    f.write("frequency,location,lat,lon,mode\n")
    for licenceId in licenceList:
        xmlfile = getUrl(acmauri + '/RegistrationSearchXML?searchField=LICENCE_NO&searchText=' + licenceId + '&ResultsLimit=2000')
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
                                lat = "0"
                                lon = "0"
                            print(str(freq) + ',' + city + ',' + lat + ',' + lon + ',' + mode)
                            csvstring = str(freq) + ',' + city + ',' + lat + ',' + lon + ',' + mode + '\n'
                            f.write(csvstring)
                            f.flush()
    f.close()


def saveData(clientId,service):
    # Open a file for STATEWIDE frequencies
    statewide = open('output/' + service + '_Statewide.csv', 'a')

    # Open a file to save the results
    lf = open('output/' + service + '.csv', 'a')

    # Loop through each site in the freqlist looking for sites inside the current poly
    with open('output/' + clientId + '.csv', newline='') as csvfile:
        data = csv.DictReader(csvfile)
        for row in data:
            if (row['location'] != 'STATEWIDE'):
                # Write out our region matching CSV
                lf.write(row['frequency'] + "," + row['location'] + "," + row['lat'] + "," + row['lon'] +"," + row['mode'] + "\n")

            if (row['location'] == 'STATEWIDE'):
                out = True
                statewide.write(row['frequency'] + "," + row['location'] + "," + row['lat'] + "," + row['lon'] +"," + row['mode'] + "\n")
    lf.close()
    statewide.close()

    # Remove all duplicates from statewide file
    uniqlines = set(open('output/' + service + '_Statewide.csv').readlines())
    bar = open('output/' + service + '_Statewide.csv', 'w').writelines(set(uniqlines))


def cleanup(service):
    fileList = glob.glob('output/' + service + '_*.csv')
    for filePath in fileList:
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
    # 391222    Airservices Australia ACT/NSW Services


    clients = [
        #{ "clientID": "20011941", "service": "ASNSW" },
        # { "clientID": "17661", "service": "ASNSW2" },
        # { "clientID": "37658", "service": "SJA" },
        # { "clientID": "20012532", "service": "SES" },
        # { "clientID": "516364", "service": "SES2" },
        # { "clientID": "20005985", "service": "RFS" },
        # { "clientID": "5832", "service": "RFS2" },
        # #{ "clientID": "20027621", "service": "OEH" },
        # #{ "clientID": "20012756", "service": "Commonwealth_Agencies" },
        # #{ "clientID": "20019469", "service": "Low_Power" },
        # { "clientID": "20008471", "service": "FRNSW" },
        # { "clientID": "20020998", "service": "RMS" },
        { "clientID": "20036348", "service": "HGSA" },
        #{ "clientID": "525851", "service": "NSWGRN" },
        # { "clientID": "115634", "service": "NPWS" },
        # { "clientID": "391222", "service": "Airservices" },
        # { "clientID": "20029221", "service": "QPRC" },
    ]

    for item in clients:
        clientId = item["clientID"]
        service = item["service"]
        print('Processing ' + clientId + ' - ' + service)
        # Clean any pre-exising output
        cleanup(service)

        # Get all licences for the client
        clientLicences = getLicences(clientId)

        # Get Freq and Site for each licence (creates CSV per client-id)
        getRegistrations(clientLicences,clientId)

        saveData(clientId,service)

        # Finally clean out any empty files in the output dir
        deleteEmptyFiles()
