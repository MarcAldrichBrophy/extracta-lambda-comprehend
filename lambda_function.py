import logging
import json
import boto3
import uuid
import base64
from io import BytesIO
from customEncoder import CustomEncoder

logger = logging.getLogger()
logger.setLevel(logging.INFO)

getMethod = "GET"
postMethod = "POST"

rootPath = "/comprehend"
healthPath = rootPath + "/health"

comprehend_client = boto3.client('comprehend')
s3_client = boto3.client('s3')
textract = boto3.client('textract')

bucket_name = 'project-1-datalake'

# main handler
def lambda_handler(event, context):
    logger.info(event)
    httpMethod = event['httpMethod']
    path = event['path']

    if httpMethod == getMethod and path == healthPath:
        response = buildResponse(200)
    elif httpMethod == postMethod and path == rootPath:
        # Analyze text using AWS Comprehend
        b64Text = json.loads(event["body"])['base64File']
        
        bytes = base64.b64decode(b64Text)
        file_obj = BytesIO(bytes)
        # Call Textract
        textract_response = textract.detect_document_text(Document={'Bytes': file_obj.getvalue()})
        # Extract text
        text = ""
        for item in textract_response["Blocks"]:
            if item["BlockType"] == "LINE":
                text += item["Text"] + " "
        
        analysis_result = analyze_text(text)
        
        upload_to_s3(text, analysis_result['Sentiment'], analysis_result)
    

        # Build a response with the analysis result
        response = buildResponse(200, analysis_result)
    else:
        response = buildResponse(404, 'Not Found')

    return response

# Analyze text using AWS Comprehend
def analyze_text(text):
    # Detect dominant language
    language_response = comprehend_client.detect_dominant_language(Text=text)
    detected_language = language_response['Languages'][0]['LanguageCode']

    # Detect sentiment
    sentiment_response = comprehend_client.detect_sentiment(Text=text, LanguageCode=detected_language)
    
    # Detect key phrases
    key_phrases_response = comprehend_client.detect_key_phrases(Text=text, LanguageCode=detected_language)
    
    key_phrases = list(set([str(phrase['Score']) for phrase in key_phrases_response['KeyPhrases']]))
    # key_phrases = [str(phrase['Score']) for phrase in key_phrases_response['KeyPhrases']
    
    # Build result dictionary
    result = {
        'DetectedLanguage': detected_language,
        'Sentiment': sentiment_response['Sentiment'],
        'SentimentScore': sentiment_response['SentimentScore'],
        'KeyPhrases': [phrase['Text'] for phrase in key_phrases_response['KeyPhrases']],
        'KeyPhraseScores': key_phrases
    }

    return result
    
    
# Upload text to S3 with sentiment as a key
def upload_to_s3(text, sentiment, analysis_result):
    #generate key
    key = uuid.uuid4().hex
    file_name = f"{sentiment}_{key}.txt"

    # Upload the text to S3
    s3_client.put_object(Body=text.encode("utf-8"), Bucket=bucket_name, Key=file_name)
    
    # Add tags to the uploaded object (include key phrases as keys and their scores as values)
    key_phrases_tags = [
        {'Key': phrase, 'Value': str(score)}
        for phrase, score in zip(analysis_result['KeyPhrases'][:8], analysis_result['KeyPhraseScores'][:8])
    ]
    seen = set()
    unique_tags = []
    for tag in key_phrases_tags:
        if tag['Key'] not in seen:
            unique_tags.append(tag)
            seen.add(tag['Key'])
            
    key_phrases_tags = unique_tags

    tag_set = [
        {'Key': 'DetectedLanguage', 'Value': analysis_result['DetectedLanguage']},
        {'Key': 'Sentiment', 'Value': analysis_result['Sentiment']},
    ] + key_phrases_tags

    print(tag_set)
    
    # Add tags to the uploaded txt
    try:
        s3_client.put_object_tagging(
            Bucket=bucket_name,
            Key=file_name,
            Tagging={'TagSet': tag_set}
        )
        print(f"Tagging successful for object {file_name}")
    except Exception as e:
        print(f"Error tagging object {file_name}: {e}")
        raise e
    
    
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
