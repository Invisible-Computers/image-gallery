# How to build an app for the Invisible Screen

## What is the invisible screen?

Check it out here: https://shop.invisible-computers.com/products/invisible-calendar


## 0. Get a developer ID

Contact us at info@invisible-computers.com and we wil provide you with a developer ID.


## 1. Define a settings url and a login url

### Login url

The user will be attempting to log in by POSTING a JWT to your **login url**.
The token contains two values:
* "user_id"
* "developer_id"
You must validate that the developer_id field matches your developer id.


You will need to respond with a temporary secret token. Your token will be included in the QUERY 
parameters of a subsequent request to your settings url. Because this token
will be part of the QUERY string, it may get logged or get stored in the users browser history. 
If your app handles private or otherwise sensitive data, you should use a one-time use token with a relatively 
short expiration time.

### Settings url 

On the **settings url**, you can serve a responsive and dynamic website that the user can use to configure your app.
If you are providing an app that displays fitness stats, you will want to guide the user through a process
to connect their fitness accounts. You will also want to provide layout configuration options for the user. 

When the user makes a GET request to your settings url, a url parameter called `?login-token=<???>` will be passed,
which will be the token that you returned from the login url. You can then set a cookie to maintain the user's session. 

Additionally, a url parameter `?device-id=<id>` is passed. 
Since a user might have multiple devices,  this to identify the device on subsequent requests. 

Last, there is a third parameter called `?&device-type=<type>`. You can use this to identify the type of device
that the user is aiming to configure with your app. 

###  Handling session timeouts on the settings url
-> Deep link into the app to re-login the user. 


## 2. Define a render url

On this url, you must serve a valid render for the device. 

On this url, the DEVICE authenticates with a JWT. The JWT will contain your developer ID. YOU MUST VALIDATE THAT THE DEVELOPER ID IS CORRECT.

The url will again have the device-id in the query parameters, as well as the device-type. 
This allows you to return a screen with setup instructions even if the user has never visited the settings url before. 

