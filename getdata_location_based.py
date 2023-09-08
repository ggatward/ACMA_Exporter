#!/usr/bin/python3
# -*- coding: utf-8 -*-

import xml.etree.ElementTree as xml
import requests, sys, os, glob
import datetime, tempfile, yaml, csv

# pip install geopandas PyShp shapely
# import geopandas as gpd
# import shapefile
# from shapely.geometry import Point, Polygon, MultiPolygon, shape

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


def getRegistrations(licenceList,clientId):
    f = open('output/' + clientId + '.csv', 'w')
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
                                lat = "0"
                                lon = "0"
                            print(str(freq) + ',' + city + ',' + lat + ',' + lon + ',' + mode)
                            csvstring = str(freq) + ',' + city + ',' + lat + ',' + lon + ',' + mode + '\n'
                            f.write(csvstring)
                            f.flush()
    f.close()


# def extractPolys(index,clientId,shpmeta,service):
#     # From:  https://gis.stackexchange.com/questions/113799/how-to-read-a-shapefile-in-python
#     polylist = []

#     # Extract specific shape id in GeoJSON format
#     data = shpdata.shapeRecords()[index]
#     area_data = data.shape.__geo_interface__
#     area_name = shpmeta['RDA'][index].replace(" ","_")
#     # Aggregate smaller areas
#     if 'Illawarra' in area_name:
#         area_name = 'NSW_South_Coast'
#     if 'Southern_Inland' in area_name:
#         area_name = 'NSW_South_Coast'
#     if 'South_Coast' in area_name:
#         area_name = 'NSW_South_Coast'
#     if 'Australian_Capital_Territory' in area_name:
#         area_name = 'NSW_South_Coast'
#     if 'Central_West' in area_name:
#         area_name = 'NSW_South_Coast'
#     if 'Central_Coast' in area_name:
#         area_name = 'Hunter_Syd'
#     if 'Hunter' in area_name:
#         area_name = 'Hunter_Syd'
#     if 'Sydney' in area_name:
#         area_name = 'Hunter_Syd'
#     if 'Northern_Inland' in area_name:
#         area_name = 'NSW_North_Coast'
#     if 'Northern_Rivers' in area_name:
#         area_name = 'NSW_North_Coast'
#     if 'Mid_North_Coast' in area_name:
#         area_name = 'NSW_North_Coast'
#     if 'Orana' in area_name:
#         area_name = 'Orana_Far_West'
#     if 'Far_West' in area_name:
#         area_name = 'Orana_Far_West'
#     if 'Riverina' in area_name:
#         area_name = 'Riverina_Murray'
#     if 'Murray' in area_name:
#         area_name = 'Riverina_Murray'

#     if 'Loddon_Mallee' in area_name:
#         area_name = 'VIC_West'
#     if 'Grampians' in area_name:
#         area_name = 'VIC_West'
#     if 'Barwon' in area_name:
#         area_name = 'VIC_West'
#     if 'Hume' in area_name:
#         area_name = 'VIC_East'
#     if 'Gippsland' in area_name:
#         area_name = 'VIC_East'

#     if 'Logan_and_Redlands' in area_name:
#         area_name = 'Brisbane'
#     if 'Brisbane_City' in area_name:
#         area_name = 'Brisbane'
#     if 'Moreton_Bay' in area_name:
#         area_name = 'Brisbane'
#     if 'Ipswich_and_West_Moreton' in area_name:
#         area_name = 'Brisbane'
#     if 'Gold_Coast' in area_name:
#         area_name = 'Brisbane'
#     if 'Sunshine_Coast' in area_name:
#         area_name = 'Wide_Bay_Burnett'

#     # If we have a MultiPolygon we need to split it into individual Polygons
#     if (shape(area_data).type == 'MultiPolygon'):
#         for polygon in shape(area_data):
#             polylist.append(polygon)
#     else:
#         polylist.append(area_data)

#     # Open a file for STATEWIDE frequencies
#     statewide = open('output/' + service + '_Statewide.csv', 'a')

#     # Loop through each polygon
#     for i in polylist:
#         # Convert poly to shapely format
#         coords = shape(i)
#         poly = Polygon(coords)

#         # Open a file to save the results
#         lf = open('output/' + service + '_' + area_name + '.csv', 'a')

#         # Loop through each site in the freqlist looking for sites inside the current poly
#         with open('output/' + clientId + '.csv', newline='') as csvfile:
#             data = csv.DictReader(csvfile)
#             for row in data:
#                 # Extract the lon/lat and set a shapely 'point'
#                 point = Point(float(row['lon']),float(row['lat']))

#                 # Check if the point is in the poly - True/False
#                 if (point.within(poly)):
#                     # Write out our region matching CSV
#                     print(row['frequency'] + " at " + row['location'] + " is in '" + area_name + "'")
#                     lf.write(row['frequency'] + "," + row['location'] + "," + row['lat'] + "," + row['lon'] +"," + row['mode'] + "\n")
#                 if (row['location'] == 'STATEWIDE'):
#                     out = True
#                     statewide.write(row['frequency'] + "," + row['location'] + "," + row['lat'] + "," + row['lon'] +"," + row['mode'] + "\n")
#         lf.close()
#     statewide.close()
#     # Remove all duplicates from statewide file
#     uniqlines = set(open('output/' + service + '_Statewide.csv').readlines())
#     #bar = open('output/' + service + '_Statewide1.csv', 'w').writelines(set(uniqlines))
#     bar = open('output/' + service + '_Statewide.csv', 'w').writelines(set(uniqlines))
#     #bar.close()



######################
# points = [[50.150874, 14.563832], [50.104217, 14.4757], [49.966785, 14.370114], [50.073802, 14.402783], [49.944036, 14.44569], [49.959517, 14.391878], [49.988219, 14.544117], [50.066673, 14.613868], [49.94696, 14.462611], [50.129684, 14.334411], [50.08892, 14.303301], [50.066749, 14.417668], [50.075101, 14.53634], [50.064396, 14.263388], [50.055027, 14.38642], [50.160055, 14.584758], [50.040627, 14.283248], [50.042484, 14.638717], [50.138972, 14.309488], [50.151947, 14.469412], [50.000437, 14.406288], [50.177643, 14.467332], [50.083176, 14.569287], [50.029644, 14.412903], [50.155166, 14.480961], [49.954799, 14.554184], [50.042168, 14.223561], [50.151349, 14.565225], [50.07656, 14.663827], [50.110211, 14.261647], [49.98352, 14.341426], [50.13142, 14.555974], [50.007052, 14.598136], [50.105399, 14.488696], [50.096282, 14.626482], [50.113605, 14.626768], [49.952213, 14.53148], [50.058545, 14.458349], [50.016023, 14.508792], [50.071948, 14.589867], [50.106051, 14.360603], [50.020599, 14.425797], [50.064876, 14.572056], [50.118254, 14.556321], [50.065982, 14.232], [50.045452, 14.217889], [50.135366, 14.335496], [50.120126, 14.633857], [50.16258, 14.41], [49.949706, 14.433877], [49.992574, 14.299198], [49.999167, 14.509118], [49.967147, 14.458644], [50.157903, 14.462958], [50.029415, 14.378698], [50.063549, 14.357676], [50.006606, 14.244327], [50.164178, 14.452357], [49.97892, 14.3269], [50.149529, 14.3472], [50.168217, 14.436196], [50.128047, 14.313571], [50.098681, 14.489209], [50.07064, 14.516238], [50.016935, 14.612858], [50.040573, 14.546343], [49.996446, 14.615458], [50.063094, 14.561846], [50.013674, 14.38807], [50.120068, 14.568918], [50.002958, 14.606296], [50.171301, 14.521588], [50.11462, 14.644043], [50.134498, 14.391158], [50.115566, 14.507894], ... ]

# input_point = (50.0875, 14.421389)

# points_filtered = []

# for point in points:
#     if distance(input_point, point).km < 1:
#         points_filtered.append(point)

# print(points_filtered)

####
def getPoints(clientId):
    # Read in data from CSV
    with open('output/' + clientId + '.csv', newline='') as csvfile:
        points = []
        data = csv.DictReader(csvfile)
        # Add all lat/lons to our points list
        for row in data:
            points.append([float(row['lat']),float(row['lon'])])

    return(points)


def groupSites(clientId,points):
    # Read in data from CSV
    with open('output/' + clientId + '.csv', newline='') as csvfile:
        data = csv.DictReader(csvfile)


        for row in data:
            points_filtered = []
            rows_filtered = []

            print(row['location'])
            # Set input_point to first lat/lon
            input_point = (float(row['lat']),float(row['lon']))
            print(input_point)

            for point in points:
                if distance(input_point, point).km < 20:
                    points_filtered.append(point)

            # print(points_filtered)

            reader = csv.reader(open('output/' + clientId + '.csv', 'r'), delimiter=",")
            for data in reader:
                # print('D2=' + data[2])
                # print('D3=' + data[3])
                for fpoint in points_filtered:
                    # print('F0=' + str(fpoint[0]))
                    # print('F1=' + str(fpoint[1]))
                # print(data[0])
                    if data[2] == str(fpoint[0]) and data[3] == str(fpoint[1]):
                        print(data)

            print("------------------")

# Find all other points in CSV within x km
# Output all these points under a single lat/lon - becomes the "site"
# rinse, repeat
# Remove duplications ??



####################################

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
    # Shapefile sample used: https://www.rda.gov.au/sites/default/files/images/rda-map-national-0920.jpg
    # infile = "shapefiles/RDA_2015_16.shp"

    # # Read in our shapefile for geo-referencing
    # shpdata = shapefile.Reader(infile)
    # # Extract data about the shapefile
    # shpmeta = gpd.read_file(infile)

#    print(shpmeta)

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
        #{ "clientID": "17661", "service": "ASNSW2" },
        #{ "clientID": "37658", "service": "SJA" },
        #{ "clientID": "20012532", "service": "SES" },
        #{ "clientID": "516364", "service": "SES2" },
        #{ "clientID": "20005985", "service": "RFS" },
        #{ "clientID": "5832", "service": "RFS2" },
        #{ "clientID": "20027621", "service": "OEH" },
        #{ "clientID": "20012756", "service": "Commonwealth_Agencies" },
        #{ "clientID": "20019469", "service": "Low_Power" },
        #{ "clientID": "20008471", "service": "FRNSW" },
        #{ "clientID": "20020998", "service": "RMS" },
        #{ "clientID": "20036348", "service": "HGSA" },
        #{ "clientID": "115634", "service": "NPWS" },
        { "clientID": "391222", "service": "Airservices_ACT_NSW" },
        #{ "clientID": "389917", "service": "Airservices_VIC_TAS" },
        #{ "clientID": "396261", "service": "Airservices_SA_NT" },
        #{ "clientID": "401054", "service": "Airservices_QLD" },
        #{ "clientID": "399343", "service": "Airservices_WA" },
        #{ "clientID": "20029221", "service": "QPRC" },
        #{ "clientID": "46975", "service": "DoD" },

    ]

    for item in clients:
        clientId = item["clientID"]
        service = item["service"]
        print('Processing ' + clientId + ' - ' + service)
        # Clean any pre-exising output
#        cleanup(service)

        # Get all licences for the client
#        clientLicences = getLicences(clientId)

        # Get Freq and Site for each licence (creates CSV per client-id)
#        getRegistrations(clientLicences,clientId)

        # Group nearby sites together
        points=getPoints(clientId)
        groupSites(clientId,points)


        # Geolocate sites and split CSV into per client-id per region
        # for index, item in enumerate(shpdata.shapeRecords()):
        #     # Area 54 (Northern Territory) seems to be corrupt - skip it.
        #     if index != 54:
        #         poly = extractPolys(int(index),clientId,shpmeta,service)

        # Finally clean out any empty files in the output dir
        deleteEmptyFiles()
