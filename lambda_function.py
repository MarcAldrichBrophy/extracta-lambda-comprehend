import logging
import json
from customEncoder import CustomEncoder

logger = logging.getLogger()
logger.setLevel(logging.INFO)

getMethod = "GET"
healthPath = "/health"

#main handler
def lambda_handler(event, context):
    logger.info(event)
    httpMethod = event['httpMethod']
    path = event['path']

    if httpMethod == getMethod and path == healthPath:
        response = buildResponse(200)
    else:
        response = buildResponse(404, 'Not Found')
    
    return response

# Response builder.
def buildResponse(statusCode, body = None):
    response = {
        'statusCode': statusCode,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        }
    }
    if body is not None:
        response['body'] = json.dumps(body, cls = CustomEncoder)
    return response