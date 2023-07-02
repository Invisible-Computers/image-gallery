# An open App Ecosystem for the Invisible Computers E-Paper Smart Display

## Motivation and Approach

Our goal is to create an app ecosystem for our [E-Paper Smart Display](https://shop.invisible-computers.com/products/invisible-calendar).

Apps run as online web services, and we users are free to decide to which apps they want to connect their display.


All apps provide a `settings url` and a `render url`. The `settings url` has to return a mobile-friendly 
html configuration, setup and settings page. The `render url` has to return an image in the correct resolution
which can be displayed on the e-paper screen.

The [Smart Display's companion app](https://www.invisible-computers.com/invisible-calendar/manual.html) navigates the user
to the settings page of any installed app, and it provides authentication and authorization via a Jason Web Token (JWT).

That's all there is to it, conceptually.

There is also a demo app that you can use as a starting point for your own app: https://github.com/Invisible-Computers/image-gallery

And we are happy to provide support for any of your questions. Please email us at: info@invisible-computers.com.

## How to build an app: A step-by-step guide

### 0. Get a developer ID

Send us a quick email info@invisible-computers.com, and we will make sure you're up and running in no time.

We will also be happy to answer any questions you have, help you along the process and may be able to advise you on your app idea. 
On an e-paper display, some types of applications work better than others. 

You can continue building your application while you're waiting for your developer ID.


### 1. Define a settings url and a JWT login url

#### JWT Login url

The user will be attempting to log in by POSTING a JWT to your **login url**.
The token contains two values:
* "user_id"
* "developer_id"
* "user_device_ids"
You must validate that the `developer_id` field matches your developer id.
You also keep track of the `user_device_ids`, such that you can later validate if the user is authorized 
to access a certain device. 


You will need to respond with a secret token. 


#### Settings url 


After this, the companion app will load your `settings url`, while passing the token in a query argument called `login-token`.

```<your-settings-url>?login-token=<the-token-you-returned>```

Because the token is part of the query string, it may get logged or get stored in the users browser history. 

If your app handles private or otherwise sensitive data, you should use a one-time use token with a relatively 
short expiration time. You can then configure the `settings url` to be a session-login url, which will redirect the 
user to the actual settings page after successful one-time-token authentication.


On the **settings page**, you should serve a mobile-friendly website that the user can use to configure your app.
For example, if you are providing an app that displays fitness stats, you will want to guide the user through a process
to connect their fitness accounts. You will also want to provide layout configuration options for the user. 

When the user makes a GET request to your settings url, a url parameter called `?login-token=<???>` will be passed,
which will be the token that you returned from the login url.

Additionally, a URL parameter `?device-id=<id>` is passed. 
Since a user might have multiple devices,  this to identify the device on subsequent requests. 

Last, there is a third parameter called `?&device-type=<type>`. You can use this to identify the type of device
that the user is aiming to configure with your app.

If you are using a one-time-token as login token, you can then set a cookie to maintain the user's session, treat this url as another login url 
and redirect the user to the "real" settings page. This is the approach taken by the [image-gallery demo app](https://github.com/Invisible-Computers/image-gallery).


####  Handling session timeouts on the settings url
-> Not fully handled yet.  Users currently have to close the page, go back to the app and click again on the "configure" button.

### 2. Define a render url

On this url, you must serve a valid render for the device. 

On this url, the DEVICE authenticates with a JWT. The JWT will contain your developer ID. YOU MUST VALIDATE THAT THE DEVELOPER ID IS CORRECT.
The JWT also contains the `user_device_ids` field, but this time, it only contains the ID of the device for which the render request is made. 

The url will have the `device_id` in the query parameters, as well as the device-type. 
This allows you to return a screen with setup instructions even if the user has never visited the settings url before. 

