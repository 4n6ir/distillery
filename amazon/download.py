import boto3
import datetime
import ipaddress
import json
import logging
import os
import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    logger.info(event)
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
    
    client = boto3.client('ssm', region_name='us-east-2')
    response = client.get_parameter(Name=os.environ['SSM_PARAMETER'])
    prevtoken = response['Parameter']['Value']
    
    r = requests.get('https://ip-ranges.amazonaws.com/ip-ranges.json')
    logger.info('Download Status Code: '+str(r.status_code))
    
    if r.status_code == 200:
        output = r.json()
        orig = datetime.datetime.fromtimestamp(int(output['syncToken']))
        new = orig + datetime.timedelta(days=33)
        if prevtoken != output['syncToken']:
            logger.info('Updating AWS IP Ranges')
            for cidr in output['prefixes']:
                sortkey = 'AWS#'+cidr['service']+'#'+cidr['region']+'#'+cidr['ip_prefix']
                hostmask = cidr['ip_prefix'].split('/')
                iptype = ipaddress.ip_address(hostmask[0])
                nametype = 'IPv'+str(iptype.version)+'#'
                iprange = cidr['ip_prefix']
                netrange = ipaddress.IPv4Network(cidr['ip_prefix'])
                first, last = netrange[0], netrange[-1]
                firstip = int(ipaddress.IPv4Address(first))
                lastip = int(ipaddress.IPv4Address(last))
                table.put_item(Item= {  'pk': nametype,
                                        'sk': sortkey,
                                        'service': cidr['service'],
                                        'region': cidr['region'],
                                        'cidr': iprange,
                                        'edge': cidr['network_border_group'],
                                        'token': int(new.timestamp()),
                                        'created': output['createDate'],
                                        'firstip': firstip,
                                        'lastip': lastip
                                    } )
            for cidr in output['ipv6_prefixes']:
                sortkey = 'AWS#'+cidr['service']+'#'+cidr['region']+'#'+cidr['ipv6_prefix']
                hostmask = cidr['ipv6_prefix'].split('/')
                iptype = ipaddress.ip_address(hostmask[0])
                nametype = 'IPv'+str(iptype.version)+'#'
                iprange = cidr['ipv6_prefix']
                netrange = ipaddress.IPv6Network(cidr['ipv6_prefix'])
                first, last = netrange[0], netrange[-1]
                firstip = int(ipaddress.IPv6Address(first))
                lastip = int(ipaddress.IPv6Address(last))
                table.put_item(Item= {  'pk': nametype,
                                        'sk': sortkey,
                                        'service': cidr['service'],
                                        'region': cidr['region'],
                                        'cidr': iprange,
                                        'edge': cidr['network_border_group'],
                                        'token': int(new.timestamp()),
                                        'created': output['createDate'],
                                        'firstip': firstip,
                                        'lastip': lastip
                                    } )
            response = client.put_parameter(Name=os.environ['SSM_PARAMETER'],
                                            Value=output['syncToken'],
                                            Type='String',
                                            Overwrite=True)
        else:
            logger.info('No AWS IP Range Updates')
    return {
        'statusCode': 200,
        'body': json.dumps('aws-ip-ranges-download')
    }
