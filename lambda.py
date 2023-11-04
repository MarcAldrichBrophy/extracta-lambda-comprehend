import boto3
import logging
import json
from customEncoder import CustomEncoder

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamoName = "IS-3150"
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(dynamoName)

getMethod = "GET"
postMethod = "POST"
deleteMethod = "DELETE"

healthPath = "/health"
productPath = "/product"
productsPath = "/products"

#main handler
def lambda_handler(event, context):
    logger.info(event)
    httpMethod = event['httpMethod']
    path = event['path']

    if httpMethod == getMethod and path == healthPath:
        response = buildResponse(200)
    elif httpMethod == postMethod and path == productPath:
        response = saveProduct(json.loads(event['body']))
    elif httpMethod == getMethod and path == productsPath:
        response = getProducts()
    elif httpMethod == getMethod and path == productPath:
        response = getProduct(event['queryStringParameters']['productId'])
    elif httpMethod == deleteMethod and path == productsPath:
        response = deleteProducts()
    else:
        response = buildResponse(404, 'Not Found')
    
    return response


def deleteProducts():
    
    try:
        response = table.scan()
        result = response['Items']

        # Delete each item individually
        for item in result:
            table.delete_item(
                Key = {
                    'productId': item['productId']
                },
                ReturnValues = 'ALL_OLD'
            )

        body = {
            'Operation': 'DELETE',
            'Message': 'SUCCESS',
            'deletedItems': result
        }
        return buildResponse(200, body)
    
    except:
        logger.exception("Error deleting all items.")
# Gets all items from the product table in DynamoDB
def getProducts():
    try:
        response = table.scan()
        result = response['Items']

        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey = response['LastEvaluatedKey'])
            result.extend(response['Items'])

        body = {
            'products': result
        }

        return buildResponse(200, body)
    except:
        logger.exception("Error getting all products.")

def getProduct(productId):
    try:
        response = table.get_item(
            Key = {
                'productId': productId
            }
        )
        if 'Item' in response:
            return buildResponse(200, response['Item'])
        else:
            return buildResponse(404, {'Message': 'id: %s not found' % productId})
    except:
        logger.exception("Error obtaining product " + str(productId) + ".")

# posts a product into dynamoDB
def saveProduct(requestBody):
    try:
        table.put_item(Item=requestBody)
        body = {
            'Operation': 'SAVE',
            'Message': 'SUCCESS',
            'Item': requestBody
        }
        return buildResponse(200, body)
    except:
        logger.exception("Error saving product.")

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

