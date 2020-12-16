import boto3
import ipaddress
import json
import os
from boto3.dynamodb.conditions import Key

def handler(event, context):
    
    ipaddr = event
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

    try:
        
        iptype = ipaddress.ip_address(ipaddr)
        
        if iptype.is_multicast == True:
            msg = 'Multicast IP Address'
        elif iptype.is_private == True:
            msg = 'Private IP Address'
        elif iptype.is_unspecified == True:
            msg = 'Unspecified IP Address'
        elif iptype.is_reserved == True:
            msg = 'Reserved IP Address'
        elif iptype.is_loopback == True:
            msg = 'Loopback IP Address'
        elif iptype.is_link_local == True:
            msg = 'Link Local IP Address'

        elif iptype.version == 4:
            
            intip = int(ipaddress.IPv4Address(ipaddr))
            
            firstlist = []
            first = table.query(
                IndexName='firstip',KeyConditionExpression=Key('pk').eq('IPv4#') & Key('firstip').lte(intip)
            )
            firstdata = first['Items']
            while 'LastEvaluatedKey' in first:
                first = table.query(
                    IndexName='firstip',KeyConditionExpression=Key('pk').eq('IPv4#') & Key('firstip').lte(intip),
                    ExclusiveStartKey=first['LastEvaluatedKey']
                )
                firstdata.update(first['Items'])
            for item in firstdata:
                firstlist.append(item['sk']+'#'+item['created'])
               
            lastlist = []
            last = table.query(
                IndexName='lastip',KeyConditionExpression=Key('pk').eq('IPv4#') & Key('lastip').gte(intip)
            )
            lastdata = last['Items']
            while 'LastEvaluatedKey' in last:
                last = table.query(
                    IndexName='lastip',KeyConditionExpression=Key('pk').eq('IPv4#') & Key('lastip').gte(intip),
                    ExclusiveStartKey=last['LastEvaluatedKey']
                )
                lastdata.update(last['Items'])
            for item in lastdata:
                lastlist.append(item['sk']+'#'+item['created'])
            
            matches = set(firstlist) & set(lastlist)
            theresults = {}
            theresults["cidrs"] = []
            for line in matches:
                parsed = line.split('#')
                linedict = {'cloud': parsed[0], 'service': parsed[1], 'region': parsed[2], 'cidr': parsed[3], 'lastseen': parsed[4]}
                theresults["cidrs"].append(linedict)
            
            msg = theresults
            
        elif iptype.version == 6:
            
            intip = int(ipaddress.IPv6Address(ipaddr))
            
            firstlist = []
            first = table.query(
                IndexName='firstip',KeyConditionExpression=Key('pk').eq('IPv6#') & Key('firstip').lte(intip)
            )
            firstdata = first['Items']
            while 'LastEvaluatedKey' in first:
                first = table.query(
                    IndexName='firstip',KeyConditionExpression=Key('pk').eq('IPv6#') & Key('firstip').lte(intip),
                    ExclusiveStartKey=first['LastEvaluatedKey']
                )
                firstdata.update(first['Items'])
            for item in firstdata:
                firstlist.append(item['sk']+'#'+item['created'])
               
            lastlist = []
            last = table.query(
                IndexName='lastip',KeyConditionExpression=Key('pk').eq('IPv6#') & Key('lastip').gte(intip)
            )
            lastdata = last['Items']
            while 'LastEvaluatedKey' in last:
                last = table.query(
                    IndexName='lastip',KeyConditionExpression=Key('pk').eq('IPv6#') & Key('lastip').gte(intip),
                    ExclusiveStartKey=last['LastEvaluatedKey']
                )
                lastdata.update(last['Items'])
            for item in lastdata:
                lastlist.append(item['sk']+'#'+item['created'])
            
            matches = set(firstlist) & set(lastlist)
            theresults = {}
            theresults["cidrs"] = []
            for line in matches:
                parsed = line.split('#')
                linedict = {'cloud': parsed[0], 'service': parsed[1], 'region': parsed[2], 'cidr': parsed[3], 'lastseen': parsed[4]}
                theresults["cidrs"].append(linedict)
                
            msg = theresults
            
    except:
        
        msg = 'Invalid IP Address'
        pass
        
    return {
        'statusCode': 200,
        'body': json.dumps(msg)
    }
