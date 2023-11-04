import logging
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)

getMethod = "GET"
healthPath = "/health"

#main handler
def lambda_handler(event):
    logger.info(event)
    httpMethod = event['httpMethod']
    path = event['path']

    if httpMethod == getMethod and path == healthPath:
        response = buildResponse(200)
    else:
        response = buildResponse(404)
    
    return response

# Response builder.
def buildResponse(statusCode):
    response = {
        'statusCode': statusCode,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        }
    }
    return response