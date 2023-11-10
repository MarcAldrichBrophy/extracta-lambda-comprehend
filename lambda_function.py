import logging
import json
import boto3
from customEncoder import CustomEncoder

logger = logging.getLogger()
logger.setLevel(logging.INFO)

getMethod = "GET"

healthPath = "/comprehend/health"
getPath = "/comprehend"

comprehend_client = boto3.client('comprehend')


# main handler
def lambda_handler(event):
    logger.info(event)
    httpMethod = event['httpMethod']
    text = event['Text']
    path = event['path']

    if httpMethod == getMethod and path == healthPath:
        response = buildResponse(200)
    elif httpMethod == getMethod and path == getPath:
        # Analyze text using AWS Comprehend
        analysis_result = analyze_text(text)

        # Build a response with the analysis result
        response = buildResponse(200, analysis_result)
    else:
        response = buildResponse(404, 'Not Found')

    return response


# Analyze text and derive sentiment using AWS Comprehend
def analyze_text(text):
    language_response = comprehend_client.detect_dominant_language(Text=text)
    detected_language = language_response['Languages'][0]['LanguageCode']

    sentiment_response = comprehend_client.detect_sentiment(Text=text, LanguageCode=detected_language)

    result = {
        'DetectedLanguage': detected_language,
        'Sentiment': sentiment_response['Sentiment'],
        'SentimentScore': sentiment_response['SentimentScore']
    }

    return result


# Response builder.
def buildResponse(statusCode, body=None):
    response = {
        'statusCode': statusCode,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        }
    }
    if body is not None:
        response['body'] = json.dumps(body, cls=CustomEncoder)
    return response
