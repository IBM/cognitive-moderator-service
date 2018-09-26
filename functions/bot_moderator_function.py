# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os
import requests
import shutil
import subprocess
import sys
import urllib

from watson_developer_cloud import NaturalLanguageUnderstandingV1
from watson_developer_cloud.natural_language_understanding_v1 import Features, EntitiesOptions, KeywordsOptions


SUPPORTED_IMAGES = ['image/jpeg', 'image/jpg', 'image/png']


# main() will be run when you invoke this action
# @param Cloud Functions actions accept a single parameter, which must be a JSON object.
# @return The output of this action, which must be a JSON object.
def main(event):
    print('Validating message...')
    print(event)
    if not verify_token(event):  # Ignore event if verification token presented doesn't match
        return

    if event.get('challenge') is not None:  # Respond to Slack event subscription verification challenge
        print('Event with verification challenge- responding accordingly...')
        challenge = event['challenge']
        return {'challenge': challenge}
        
    event_details = event['event']
    channel = event_details['channel']
    
    if contain_image(event):  # Ignore event if Slack message doesn't contain any images
        file_details = event_details['files'][0]
        image_url = file_details['url_private']
            
        file_id = file_details['id']
        
        print('Downloading image...')
        image_bytes = download_image_requests(event,image_url)
        print('Saving image locally ...')
        # with open('./file.jpg', 'wb') as jpgFile:
        #   jpgFile.write(image_bytes)
        
        with open('./file.jpg', 'wb') as jpgFile:
            image_bytes.raw.decode_content = True    
            shutil.copyfileobj(image_bytes.raw, jpgFile)
            
        subprocess.call(["ls", "-l", "file.jpg"])
        
        print('Checking image for explicit content...' + image_url)  
            
        with open('./file.jpg', 'rb') as image_file:
            classes = requests.post(
                'https://gateway.watsonplatform.net/visual-recognition/api/v3/classify',
                auth=('apikey', event['VISUAL_RECOGNITION_IAM_APIKEY']),
                files={'images_file': image_file},
                params={
                    'version': '2016-05-20',
                    'classifier_ids': 'explicit'})
            
        print('image classified for explicit content')
        response_classes = classes.json();        
        print(response_classes)
        is_explicit = False
        print(response_classes['images'][0]['classifiers'])
            
        for i in response_classes['images'][0]['classifiers']:
            if i['classifier_id'] == 'explicit':
                print(i['classes'][0]['class'])
                if i['classes'][0]['class'] == 'explicit':
                    is_explicit = True            
        
        if is_explicit:
            print('Image displays explicit content- deleting from Slack Shared Files...')
            delete_image(event, file_id)
            print('Posting message to channel to notify users of file deletion...')
            post_message(event, channel, "File removed due to contain explicit content")
            
        return {"payload": "Done"}
        
    message_text = event_details.get('text')
    event_subtype = event_details.get('subtype')
    
    # skip reply messages sent from bot
    if event_subtype == 'bot_message':
        return {"payload": "Done"}
    
    if message_text:
        print('Text Message:' + message_text)
        natural_language_understanding = NaturalLanguageUnderstandingV1(
            username=event['NLU_USERNAME'],
            password=event['NLU_PASSWORD'],
            version='2018-03-16')

        response = natural_language_understanding.analyze(
        text=message_text,
        features=Features(
                entities=EntitiesOptions(
                emotion=True,
                sentiment=True,
                limit=2),
            keywords=KeywordsOptions(
                emotion=True,
                sentiment=True,
                limit=2))
            )
        
        print('response:'+json.dumps(response, indent=2))
        
        keyword = response.get('keywords')
        #print('keywords:'+keyword)
        
        if keyword:
            print('keywords:'+keyword[0]['text'])
            disgust = response['keywords'][0]['emotion']['disgust']
            anger = response['keywords'][0]['emotion']['anger']
            print(disgust)
            print(anger)
            if disgust>.5 or anger>.5:
                print('In appropriate text.....')
                post_message(event,channel,"please be more polite ...")
    
    return {"payload": "Done"}


def verify_token(event):
    if event['token'] != event['SLACK_VERIFICATION_TOKEN']:
        print('Presented with invalid token- ignoring message...')
        return False
    return True


def post_message(event,channel, text):
    url = event['SLACK_MESSAGE_POST_URL']
    data = urllib.parse.urlencode(
        (
            ("token", event['SLACK_ACCESS_TOKEN']),
            ("channel", channel),
            ("text", text)
        )
    )
    data = data.encode("ascii")
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    request = urllib.request.Request(url, data, headers)
    response = urllib.request.urlopen(request)
    print('Slack response: '+json.dumps(response.read().decode('utf-8'), indent=2))

    
def contain_image(event):
    event_details = event['event']
    file_subtype = event_details.get('subtype')

    if file_subtype != 'file_share':
        print('Not a file event, ignoring event...')
        return False

    file_details = event_details['files']
    mime_type = file_details[0]['mimetype']
    file_size = file_details[0]['size']
    
    if mime_type not in SUPPORTED_IMAGES:
        print('File is not an image, ignoring event...')
        return False

    return True


def download_image_requests(event,url):
    response = requests.get(url,stream=True, headers={'Authorization': 'Bearer %s' % event['SLACK_ACCESS_TOKEN']})
    return response


def delete_image(event,file_id):
    url = event['SLACK_MESSAGE_DELETE_URL']
    data = urllib.parse.urlencode(
        (
            ("token", event['SLACK_ACCESS_TOKEN']),
            ("file", file_id)
        )
    )
    data = data.encode("ascii")
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    request = urllib.request.Request(url, data, headers)
    urllib.request.urlopen(request)
