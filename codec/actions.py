import requests
import xmltodict
from lxml import etree
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

codec_username = 'admin'
codec_password = 'Trucks08!'

def get_status(host):
    url = 'https://{}/getxml?location=/Status/Standby'.format(host)
    try:
        response = requests.get(url, verify=False, timeout=2, auth=(codec_username, codec_password))
        xmlstr = response.content
        root = etree.fromstring(xmlstr)
        status = root.xpath('//Status/Standby/State/text()')[0]
        return(status)
    except:
        return("Down")
        
def get_all(host):
    url = 'https://{}/getxml?location=/Status/'.format(host)
    try:
        response = requests.get(url, verify=False, timeout=2, auth=(codec_username, codec_password))
        xml_dict = xmltodict.parse(response.content)
        return(xml_dict)
    except:
        return None
        
def get_sip(host):
    url = 'https://{}/getxml?location=/Status/SIP/Registration'.format(host)
    try:
        response = requests.get(url, verify=False, timeout=2, auth=(codec_username, codec_password))
        xmlstr = response.content
        root = etree.fromstring(xmlstr)
        status = root.xpath('//Status/SIP/Registration/Status/text()')[0]
        return(status)
    except:
        return("Down")

def get_people(host):
    url = 'https://{}/getxml?location=/Status/RoomAnalytics'.format(host)
    try:
        response = requests.get(url, verify=False, timeout=2, auth=(codec_username, codec_password))
        xml_dict = xmltodict.parse(response.content)
        check = xml_dict["Status"]["RoomAnalytics"]["PeopleCount"]
        if check != "None":
            return check["Current"]
    except:
        return None
        
#def get_call_status(host):
#    <Status product="Cisco Codec" version="ce9.9.2.f2110f7eda7" apiVersion="4">
#    <Call item="14" maxOccurrence="n">
#    <AnswerState>Answered</AnswerState>
#    <CallType>Video</CallType>
#    <CallbackNumber>sip:+15037459997@freightliner.com</CallbackNumber>
#    <DeviceType>Endpoint</DeviceType>
#    <Direction>Outgoing</Direction>
#    <DisplayName>Jeremy Worden</DisplayName>
#    <Duration>3886</Duration>
#    <Encryption>
#    <Type>None</Type>
#    </Encryption>
#    <FacilityServiceId>0</FacilityServiceId>
#    <HoldReason>None</HoldReason>
#    <Ice>Disabled</Ice>
#    <PlacedOnHold>False</PlacedOnHold>
#    <Protocol>SIP</Protocol>
#    <ReceiveCallRate>6000</ReceiveCallRate>
#    <RemoteNumber>+15037459997@freightliner.com</RemoteNumber>
#    <Status>Connected</Status>
#    <TransmitCallRate>1500</TransmitCallRate>
#    </Call>
#    </Status>

def get_loss(host):
    url = 'https://{}/getxml?location=/Status/MediaChannels'.format(host)
    
    video ={
        'totalin':'',
        'totalout':''
    }
    
    audio ={
        'totalin':'',
        'totalout':''
    }
    
    try:
        response = requests.get(url, verify=False, timeout=2, auth=(codec_username, codec_password))
        xml_dict = xmltodict.parse(response.content)
    except:
        return video, audio
    try:
        check = xml_dict["Status"]["MediaChannels"]
        if check != "None":
            channels = xml_dict["Status"]["MediaChannels"]["Call"]["Channel"]
            for channel in channels:
                if "Video" in channel.keys() and channel["Video"]["ChannelRole"] == "Main":
                    direction = channel["Direction"]
                    if direction == "Incoming":
                        lossin = float(channel["Netstat"]["Loss"])
                        pksin = float(channel["Netstat"]["Packets"])

                        if lossin == 0:
                            totalin = 0
                        else:
                            totalin = (lossin/pksin)* 100
                            
                        video['totalin'] = round(totalin, 2)
                    else:
                        lossout = float(channel["Netstat"]["Loss"])
                        pksout = float(channel["Netstat"]["Packets"])

                        if lossout == 0:
                            totalout = 0
                        else:
                            totalout = (lossout / pksout) * 100
                            
                        video['totalout'] = round(totalout, 2)
    except:
        video['totalout'] = 0
        video['totalin'] = 0
        
    try:
        check = xml_dict["Status"]["MediaChannels"]
        if check != "None":
            channels = xml_dict["Status"]["MediaChannels"]["Call"]["Channel"]
            for channel in channels:
                if "Audio" in channel.keys() and channel["Type"] == "Audio":
                    direction = channel["Direction"]
                    if direction == "Incoming":
                        lossin = float(channel["Netstat"]["Loss"])
                        pksin = float(channel["Netstat"]["Packets"])

                        if lossin == 0:
                            totalin = 0
                        else:
                            totalin = (lossin/pksin)* 100
                            
                        audio['totalin'] = round(totalin, 2)
                    else:
                        lossout = float(channel["Netstat"]["Loss"])
                        pksout = float(channel["Netstat"]["Packets"])

                        if lossout == 0:
                            totalout = 0
                        else:
                            totalout = (lossout/pksout)* 100
                            
                        audio['totalout'] = round(totalout, 2)
    except:
        audio['totalout'] = 0
        audio['totalin'] = 0
        
    return video, audio

def get_diag(host):
    url = 'https://{}//getxml?location=/Status/Diagnostics'.format(host)
    try:
        diagresponse = requests.get(url, verify=False, timeout=2, auth=(codec_username, codec_password))
        xmlstr = diagresponse.content
        root = etree.fromstring(xmlstr)
        diag = root.xpath('//Status/Diagnostics/Message/Description/text()')
        diag = [l for l in diag if l != 'No camera is detected']
        if len(diag) == 0:
            diag = "None"
        else:
            diag = root.xpath('//Status/Diagnostics/Message/Description/text()')
        return (diag)
    except:
        return("None")

def get_last(host):
    url = 'https://{}/putxml'.format(host)
    payload = last
    headers = {'Content-Type': 'text/xml'}
    try:
        lastcallfromcodec = requests.post(url, data=payload, verify=False, timeout=2, headers=headers, auth=(codec_username, codec_password))
        xmlstr = lastcallfromcodec.text
        root = etree.fromstring(xmlstr)
        callinfo = root.xpath('//Entry/RemoteNumber/text()')[0]
        callinfo += ", " + root.xpath('//Entry/StartTime/text()')[0]
        duration = int(float(root.xpath('//Entry/Duration/text()')[0])/60)
        callinfo += ", " + str(duration)
        callinfo += ", " + root.xpath('//Entry/Video/Incoming/PacketLossPercent/text()')[0]
        callinfo += "/" + root.xpath('//Entry/Video/Outgoing/PacketLossPercent/text()')[0]
        callinfo += ", " + root.xpath('//Entry/Audio/Incoming/PacketLossPercent/text()')[0]
        callinfo += "/" + root.xpath('//Entry/Audio/Outgoing/PacketLossPercent/text()')[0]
        return (callinfo)
    except:
        return ("Failed getting last call info")