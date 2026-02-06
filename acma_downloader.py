#!/usr/bin/python3
# -*- coding: utf-8 -*-

from json.tool import main
from re import S
import xml.etree.ElementTree as xml
import requests, os, glob, time

# pip install geopy
# from geopy.distance import distance

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


def parseXML1(xmlfile):
    tree1 = xml.parse(xmlfile)
    root1 = tree1.getroot()
    return root1


def getLicences(clientId,offset):
    licenceList = []
    xmlfile = getUrl(acmauri + '/LicenceSearchXML?searchText=' + clientId + '&offset=' + str(offset) + '&ResultsLimit=2000')

    # Parse the XML
    root = parseXML('/tmp/xmlfile.xml')

    if root is None:
        print('no xml')
        return

### TODO:  Handle this:
# <?xml version="1.0" encoding="utf-8"?>
# <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
# <html xmlns="http://www.w3.org/1999/xhtml">
#   <head>
#     <title>Request Error</title>
#     <style>BODY { color: #000000; background-color: white; font-family: Verdana; margin-left: 0px; margin-top: 0px; } #content { margin-left: 30px; font-size: .70em; padding-bottom: 2em; } A:link { color: #336699; font-weight: bold; text-decoration: underline; } A:visited { color: #6699cc; font-weight: bold; text-decoration: underline; } A:active { color: #336699; font-weight: bold; text-decoration: underline; } .heading1 { background-color: #003366; border-bottom: #336699 6px solid; color: #ffffff; font-family: Tahoma; font-size: 26px; font-weight: normal;margin: 0em 0em 10px -20px; padding-bottom: 8px; padding-left: 30px;padding-top: 16px;} pre { font-size:small; background-color: #e5e5cc; padding: 5px; font-family: Courier New; margin-top: 0px; border: 1px #f0f0e0 solid; white-space: pre-wrap; white-space: -pre-wrap; word-wrap: break-word; } table { border-collapse: collapse; border-spacing: 0px; font-family: Verdana;} table th { border-right: 2px white solid; border-bottom: 2px white solid; font-weight: bold; background-color: #cecf9c;} table td { border-right: 2px white solid; border-bottom: 2px white solid; background-color: #e5e5cc;}</style>
#   </head>
#   <body>
#     <div id="content">
#       <p class="heading1">Request Error</p>
#       <p>The server encountered an error processing the request. The exception message is 'The request channel timed out while waiting for a reply after 00:00:59.9950045. Increase the timeout value passed to the call to Request or increase the SendTimeout value on the Binding. The time allotted to this operation may have been a portion of a longer timeout.'. See server logs for more details. The exception stack trace is: </p>
#       <p>
# Server stack trace:
#    at System.ServiceModel.Channels.RequestChannel.Request(Message message, TimeSpan timeout)
#    at System.ServiceModel.Dispatcher.RequestChannelBinder.Request(Message message, TimeSpan timeout)
#    at System.ServiceModel.Channels.ServiceChannel.Call(String action, Boolean oneway, ProxyOperationRuntime operation, Object[] ins, Object[] outs, TimeSpan timeout)



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
                    city = "NONE"
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


def getRegistrations(licenceList,clientId,system,offset,widetag):
    if (offset == '0'):
        action = 'w'
    else:
        action = 'a'
    f = open('downloads/' + favourite + '_' + system + '_' + clientId + '.csv', action)
    if clientId == "46975":
        g = open('downloads/Aviation_' + system + '_' + clientId + '.csv', action)
        g.write("frequency,location,lat,lon,mode,alphatag\n")
    # Write our CSV header
    if (offset == '0'):
        f.write("frequency,location,lat,lon,mode,alphatag\n")
    for licenceId in licenceList:
        xmlfile = getUrl(acmauri + '/RegistrationSearchXML?searchField=LICENCE_NO&searchText=' + licenceId + '&offset=' + str(offset) + '&ResultsLimit=2000')
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
                                mode = registrationData.text.strip()
                            if (registrationData.tag == 'DEVICE_TYPE_TEXT'):
                                # Only get Repeater/Base Transmit allocations
                                if (registrationData.text == 'Transmitter'):
                                    isTx = True
                        if (isTx):
                            if (site != ''):
                                (city,lat,lon,name) = getSites(site)
                                time.sleep(1)
                            else:
                                if (widetag == 'NATIONAL'):
                                    city = "NATIONWIDE"
                                    lat = "-27.84"
                                    lon = "133.21"
                                    # range 4500mi
                                elif (widetag == 'NSW'):
                                    city = "NSW-WIDE"
                                    lat = "-31.9737"
                                    lon = "147.7538"
                                    # range 450mi
                                elif (widetag == 'VIC'):
                                    city = "VIC-WIDE"
                                    lat = "-36.6535"
                                    lon = "144.8534"
                                    # range 200mi
                                elif (widetag == 'QLD'):
                                    city = "QLD-WIDE"
                                    lat = "-20.2600"
                                    lon = "146.4869"
                                    # range 750mi
                                elif (widetag == 'SA'):
                                    city = "SA-WIDE"
                                    lat = "-32.1365"
                                    lon = "134.8854"
                                    # Range 500mi
                                elif (widetag == 'WA'):
                                    city = "WA-WIDE"
                                    lat = "-23.763154"
                                    lon = "119.768237"
                                    # range = 825mi
                                elif (widetag == 'NT'):
                                    city = "NT-WIDE"
                                    lat = "-18.852156"
                                    lon = "133.479175"
                                    # range = 560mi
                                elif (widetag == 'TAS'):
                                    city = "TAS-WIDE"
                                    lat = "-41.539774"
                                    lon = "146.223315"
                                    # range = 190mi
                                else:
                                    city = "STATEWIDE"
                                    lat = "0.0"
                                    lon = "0.0"
                            print(str(freq) + ',' + city + ',' + lat + ',' + lon + ',' + mode + ',')
                            csvstring = str(freq) + ',' + city + ',' + lat + ',' + lon + ',' + mode + ',\n'
                            # Ignore HF and SHF
                            if float(freq) < 30 or float(freq) > 1300:
                                continue
                            # For DoD split out airband seperately
                            if clientId == "46975":
                                if float(freq) > 118 and float(freq) < 137:
                                    g.write(csvstring)
                                    g.flush()
                                    continue
                            f.write(csvstring)
                            f.flush()
                    time.sleep(1)
    f.close()


def cleanup(favourite,system,clientId):
    csvFileList = glob.glob('downloads/' + favourite + '_' + system + '_' + clientId + '.csv')
    for filePath in csvFileList:
        try:
            os.remove(filePath)
        except:
            print("Error while deleting file : ", filePath)



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
    #   15 = Aviation
    #   20 = Railroad
    #   21 = Other
    #   30 = Military
    #  208 = Custom1

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
        #
        # { "clientID": "20008471", "favourite": "NSW EMS", "system": "FRNSW", "service_type": "3", "syskey": "0", "range": "25", "widetag": "NSW", "system_type": "CONV" },
        # { "clientID": "20005985", "favourite": "NSW EMS", "system": "RFS", "service_type": "3", "syskey": "1", "range": "25", "widetag": "NSW", "system_type": "CONV" },
        # { "clientID": "CUSTOM", "favourite": "NSW EMS", "system": "RFS FG", "service_type": "8", "syskey": "2", "range": "25", "widetag": "NSW", "system_type": "CONV", "colour": "Red" },
        # { "clientID": "20011941", "favourite": "NSW EMS", "system": "ASNSW", "service_type": "4", "syskey": "3", "range": "25", "widetag": "NSW", "system_type": "CONV" },
        # { "clientID": "20012532", "favourite": "NSW EMS", "system": "SES", "service_type": "1", "syskey": "4", "range": "25", "widetag": "NSW", "system_type": "CONV" },
        #
        # { "clientID": "115634", "favourite": "NSW MISC", "system": "NPWS", "service_type": "208", "syskey": "0", "range": "25", "widetag": "NSW", "system_type": "CONV" },
        # { "clientID": "45451", "favourite": "NSW Rail", "system": "ZigZag", "service_type": "20", "syskey": "0", "range": "25", "widetag": "NSW", "system_type": "CONV" },

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
        { "clientID": "210019", "favourite": "VIC EMS", "system": "CFA", "service_type": "3", "syskey": "1", "range": "25", "widetag": "VIC", "system_type": "CONV" },
        { "clientID": "446656", "favourite": "VIC EMS", "system": "CFA", "service_type": "3", "syskey": "1", "range": "25", "widetag": "VIC", "system_type": "CONV" },
        # { "clientID": "159075", "favourite": "VIC EMS", "system": "AMBVIC", "service_type": "4", "syskey": "3", "range": "25", "widetag": "VIC", "system_type": "CONV" },
        # { "clientID": "159095", "favourite": "VIC EMS", "system": "SES", "service_type": "1", "syskey": "4", "range": "25", "widetag": "VIC", "system_type": "CONV" },

        # { "clientID": "1310687", "favourite": "VIC Rail", "system": "VicRail", "service_type": "20", "syskey": "0", "range": "25", "widetag": "VIC", "system_type": "CONV" },
        # { "clientID": "1141005", "favourite": "VIC Rail", "system": "VicRail", "service_type": "20", "syskey": "0", "range": "25", "widetag": "VIC", "system_type": "CONV" },
        # { "clientID": "20041674", "favourite": "VIC Rail", "system": "Puffing Billy", "service_type": "20", "syskey": "1", "range": "25", "widetag": "VIC", "system_type": "CONV" },


        ########################
        # { "clientID": "1507321", "favourite": "SA GRN", "system": "SA GRN", "service_type": "21", "syskey": "0", "range": "25", "widetag": "SA", "system_type": "P25" },

        # { "clientID": "169283", "favourite": "SA EMS", "system": "CFS", "service_type": "3", "syskey": "1", "range": "25", "widetag": "SA", "system_type": "CONV" },

        # { "clientID": "1500993", "favourite": "SA Rail", "system": "Pichi Richi", "service_type": "20", "syskey": "0", "range": "25", "widetag": "SA", "system_type": "CONV" },


        ########################
        # { "clientID": "192835", "favourite": "WA EMS", "system": "DFESWA", "service_type": "3", "syskey": "1", "range": "25", "widetag": "WA", "system_type": "CONV" },
        # { "clientID": "206335", "favourite": "WA EMS", "system": "DFESWA", "service_type": "3", "syskey": "1", "range": "25", "widetag": "WA", "system_type": "CONV" },

        # { "clientID": "1147725", "favourite": "WA Rail", "system": "Hotham Valley", "service_type": "20", "syskey": "0", "range": "25", "widetag": "WA", "system_type": "CONV" },

        ########################
        # { "clientID": "180004", "favourite": "NT EMS", "system": "NTPOL", "service_type": "2", "syskey": "5", "range": "25", "widetag": "NT", "system_type": "CONV" },

    ]


    for item in clients:
        clientId = item["clientID"]
        favourite = item["favourite"]
        system = item["system"]
        service_type = item["service_type"]
        syskey = item["syskey"]
        range = item["range"]
        widetag = item["widetag"]
        print('Processing ' + clientId + ' - ' + system)

        # Clean any pre-exising output
        cleanup(favourite,system,clientId)

        if clientId != "CUSTOM":
            # Get all licences for the client
            offset = '0'
            clientLicences = getLicences(clientId,offset)

            # Get Freq and Site for each licence (creates CSV per client-id)
            offsets = ['0', '2000', '4000']
            for offset in offsets:
                getRegistrations(clientLicences,clientId,system,offset,widetag)
