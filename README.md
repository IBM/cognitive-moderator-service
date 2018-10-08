# Create a cognitive moderator chatbot for anger detection, natural language understanding and explicit images removal
In this code pattern, we will create a chatbot using IBM functions and Watson services. The chatbot flow will be enhanced by using Visual Recognition and Natural Language Understanding to identify and remove explicit images and or detect anger and ugly messages 

When the reader has completed this journey, they will understand how to:

* Create a chatbot that integrates with Slack via IBM Functions
* Use Watson Visual Recognition to detect explicit images (in beta)
* Use Watson Natural Understanding to detect emotions in a conversation
* Identify entities with Watson Natural Language Understanding

![](doc/source/images/architecture.png)

## Flow
1. The user interacts from the Slack app and either sends a text or uploads an image.
2. The text or image that is used in the Slack for conversation is then passed to an IBM function API by a bot. The API is a call to an IBM Function that categorizes the text or images based on the response of Watson Visual Recognition or Watson Natural Language Processing.
3. Watson Visual Recognition categorizes the uploaded image using default and explicit classifier.
4. Watson Natural Language Processing categorizes the text, if text is send as part of slack communication.
5. IBM function then gets the response and if the text is not polite, a message is sent by the bot to the Slack user to be more polite using [Slack post message API](https://api.slack.com/methods/chat.postMessage). If the image used is explicit, the image will be deleted by the IBM function using [Slack files delete API](https://api.slack.com/methods/files.delete).


## Included components

* [IBM Functions](https://console.bluemix.net/openwhisk/): IBM Cloud Functions (based on Apache OpenWhisk) is a Function-as-a-Service (FaaS) platform which executes functions in response to incoming events and costs nothing when not in use.
* [IBM Watson Visual Recognition](https://www.ibm.com/watson/services/visual-recognition/): Quickly and accurately tag, classify and train visual content using machine learning.
* [IBM Watson Natural Language Understanding](https://www.ibm.com/watson/developercloud/natural-language-understanding.html): Analyze text to extract meta-data from content such as concepts, entities, keywords, categories, sentiment, emotion, relations, semantic roles, using natural language understanding.

## Featured technologies

* [Slack Apps](https://api.slack.com/slack-apps) Customize functionality for your own workspace or build a beautiful bot to share with the world.
* [Slack Bots](https://api.slack.com/bot-users) Enable conversations between users and apps in Slack by building bots.

# Watch the Video

[![](http://img.youtube.com/vi/9c7NuamK8JA/0.jpg)](https://youtu.be/9c7NuamK8JA)


# Steps

1. [Clone the repo](#1-clone-the-repo)
2. [Create Watson Visual Recognition and Natural Language Understanding service with IBM Cloud](#2-create-watson-visual-recognition-and-natural-language-understanding-service-with-ibm-cloud)
3. [Create Slack App and Bot for a workspace](#3-create-slack-app-and-bot-for-a-workspace)
4. [Deploy the function to IBM Cloud](#4-deploy-the-function-to-ibm-cloud)
5. [Test using slack](#5-test-using-slack)


## 1. Clone the repo

Clone the `cognitive-moderator-service` repo locally. In a terminal, run:

```
$ git clone https://github.com/IBM/cognitive-moderator-service.git
$ cd cognitive-moderator-service
```

## 2. Create Watson Visual Recognition and natural language understanding service with IBM Cloud

If you do not already have a IBM Cloud account, [sign up for IBM Cloud](https://console.bluemix.net/registration).
Create the following services:

* [**Watson Visual Recognition**](https://console.bluemix.net/catalog/services/visual-recognition)
* [**Watson Natural Language Understanding**](https://console.bluemix.net/catalog/services/natural-language-understanding) 

> Make note of the service credentials when creating services which will be later used when creating a function.

## 3. Create Slack App and Bot for a workspace

* Go to Your Apps using the following link: https://api.slack.com/apps and click `Create New App` and fill out the `App Name` and the `Workspace` you would like to use it for and click `Create App`.

![](doc/source/images/create-new-app.png)

* After the app is created, you will be taken to a page where you can configure the Slack app. Make note of **`Verification Token`**  which will be used later in the function.
![](doc/source/images/app-credentials.png)

* Add `Event Subscriptions` for your app by clicking on to `Add features and functionality` from the main page of the app.
![](doc/source/images/event-subscriptions.png)

In the `Event Subscriptions` page, enable it by turning `on` using the `on/off` toggle button and `Add Workspace and Bot Events` in subsequent sections. Add Following events for both:

1. message.channels
2. message.group
3. message.im

![](doc/source/images/events.png)

* For now leave the `Request URL` empty. We will fill it in when the `IBM Cloud Function` is exposed through an API.

* From `OAuth and Permissions`, Save the `OAuth Access Token` and `Bot User OAuth Access Token` for later use by the IBM cloud function.
![](doc/source/images/oauth-access-token.png)

Select `Permissions Scopes` that will be used by the bot that we will be creating next.

![](doc/source/images/permission-scopes.png)

* Create bot user from `Bot Users`. Provide a `Display Name` and `Default Username` for the bot and click `Save Changes`.
![](doc/source/images/bot-users.png)

* Once this is done make sure you `reinstall or install app` from Install App section.
![](doc/source/images/reinstall-app.png)

## 4. Deploy the function to IBM Cloud
Once the credentials for both IBM Cloud and Slack are noted, we can now deploy the function to IBM Cloud.

copy `params.sample.json` to `params.json` using `cp params.sample.json params.json` and replace the values with the credentials you have noted in proper place holders.

```
{
    "NLU_USERNAME": "<NLU username>",
    "NLU_PASSWORD": "<NLU password>",

    "VISUAL_RECOGNITION_IAM_APIKEY": "<Visual Recognition IAM API Key>",

    "SLACK_VERIFICATION_TOKEN": "<Slack Verification Token>",
    "SLACK_ACCESS_TOKEN": "<Slack OAuth Access Token>",

    "SLACK_MESSAGE_POST_URL": "https://slack.com/api/chat.postMessage",
    "SLACK_MESSAGE_DELETE_URL": "https://slack.com/api/files.delete"
}

```

Make sure IBM cloud CLI are installed if you haven't already using the following link: 
https://console.bluemix.net/docs/cli/index.html#overview

* Deploy the function to IBM cloud. Make sure you are in the project directory then, from Terminal run:

```
ibmcloud wsk action create WatsonModerator functions/bot_moderator_function.py --param-file params.json --kind python-jessie:3

```
* After the function is created, you can run following command to update the function if there are any changes:

```
ibmcloud wsk action update WatsonModerator functions/bot_moderator_function.py --param-file params.json --kind python-jessie:3
```

Now you can login to IBM cloud and see the function by going to `IBM functions`, click `Actions`. You should see the function in the list of function in this page.
![](doc/source/images/ibm-cloud-functions.png)


* Expose the function so that it can be accessed using an API

1. Click the `APIs` from the IBM Cloud Functions page and click  `Create Managed API`.
![](doc/source/images/create-api.png)

2. Provide `API Name`, `Base path for API`
![](doc/source/images/create-api-1.png)

3. Click `Create Operation` and in the dialog box that appears, provide the following like in the figure below:
![](doc/source/images/create-api-2.png)

4. From the `API Explorer` select the `API Url` and add the URL to the `Request URL` in Slack App you created in above steps.
![](doc/source/images/create-api-3.png)

> Note that you need to `Reinstall App` after you make any changes to the app for example: `Request URL`.

![](doc/source/images/request-url.png)

> Make sure the URL is verified. To be verified the API needs to return a response to the request that Slack sends to this `Request URL` with `challenge` parameter.


## 5. Test using slack

* **Test Case 1: Usage of rude messages**

Now you can use slack to test. If rude message are sent which NLU categorized as `anger` or `disgust` you will see a message from the `bot` that you created from Slack.

![](doc/source/images/slack-test-1.png)

* **Test Case 2: Usage of explicit image**

Upload an image that's explicit. 

> An explicit image is an image that contains objectionable or adult content that may be unsuitable for general audiences.

When you upload an **explicit** image, the image will be deleted from the Slack conversation.

![](doc/source/images/explicit-photo-upload.png)

![](doc/source/images/explicit-photo-upload-2.png)

# Sample Output

![](video/Bot4Code.gif)

## Troubleshooting

* You can monitor logs and see the output of the each request and/or call to function from the `monitor` page of the function.
![](doc/source/images/monitor-function.png)

* You can change the code at runtime and run the function, by clicking `Code` from left navigation menu of the function page. It will open up an editor with the code which you can change and save. To run click `Invoke`.
![](doc/source/images/code-editor.png)

* You can also change parameters at runtime by clicking `Parameters` from left navigation menu of the function page.
![](doc/source/images/parameters.png)

# Links

* [IBM Cloud Functions](https://console.bluemix.net/docs/openwhisk/index.html#getting-started-with-cloud-functions) - Getting started with IBM Cloud functions
* [Watson Node.js SDK](https://github.com/watson-developer-cloud/node-sdk): Visit the Node.js library to access IBM Watson services.
* [Sample Node.js application for Language Translator](https://github.com/watson-developer-cloud/language-translator-nodejs): Sample Node.JS application for Watson Language Translator service


# Learn more

* **Artificial Intelligence Code Patterns**: Enjoyed this Code Pattern? Check out our other [AI Code Patterns](https://developer.ibm.com/code/technologies/artificial-intelligence/).
* **AI and Data Code Pattern Playlist**: Bookmark our [playlist](https://www.youtube.com/playlist?list=PLzUbsvIyrNfknNewObx5N7uGZ5FKH0Fde) with all of our Code Pattern videos
* **With Watson**: Want to take your Watson app to the next level? Looking to utilize Watson Brand assets? [Join the With Watson program](https://www.ibm.com/watson/with-watson/) to leverage exclusive brand, marketing, and tech resources to amplify and accelerate your Watson embedded commercial solution.

# License
[Apache 2.0](LICENSE)
