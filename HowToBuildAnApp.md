# An Open App Ecosystem for the Invisible Computers E-Paper Smart Display

## Motivation and Approach

Our goal is to create an app ecosystem for our [E-Paper Smart Display](https://shop.invisible-computers.com/products/invisible-calendar).

Apps run as online web services, and add them to their display.


All apps provide a `settings url` and a `render url`. The `settings url` has to return a mobile-friendly 
html configuration, setup and settings page. The `render url` has to return an image in the correct resolution
which can be displayed on the e-paper screen.

The [Smart Display's companion app](https://www.invisible-computers.com/invisible-calendar/manual.html) navigates the user
to the settings page of any installed app, and it provides authentication and authorization via a Jason Web Token (JWT).

That's all there is to it, conceptually.

There is also a demo app that you can use as a reference for your own app: https://github.com/Invisible-Computers/image-gallery

And we are happy to provide support for any of your questions. Please email us at: info@invisible-computers.com.

## How to build an app: A step-by-step guide

### 0. Get a developer ID

Send us a quick email info@invisible-computers.com, and we will make sure you're up and running in no time.

We will also be happy to answer any questions you have, help you along the process and may be able to advise you on your app idea. 
On an e-paper display, some types of applications work better than others. 

You can continue building your application while you're waiting for your developer ID.


### 1. Define a settings url and a JWT login url

#### JWT Login url

When the users opens your settings page via the Invisible-Computers app, they will be posting a JWT to your **login url**.
The token contains the following values:
* `user_id`
* `developer_id`
* `device_id`
* `installation_id`
You must validate that the `developer_id` field matches your developer id, to prevent developers of other
applications from impersonating your users. 
Installation IDs are globally unique, but there can be multiple installations of your app on a single device.

You may choose to simply identify sessions by `installation_id`, or you may choose to keep track of devices and users.

You will need to respond with a JSON dict containing a secret authentication token. 

```{"login_token": auth_token}```


After this, the companion app will load your `settings start url`, while passing the token in a query argument called `login-token`.

```<your-settings-start-url>/?login-token=<the-token-you-returned>&device-type=<device-type>```

Because the token is part of the query string, it may get logged or get stored in the users browser history.

If your app handles private or otherwise sensitive data, you should use a one-time use token with a relatively 
short expiration time. You can then use the `settings start url` as a `session login url`, 
which will redirect to the actual settings page after successful one-time-token authentication.

On the settings page, you should serve a mobile-friendly website that the user can use to configure your app.
For example, if you are providing an app that displays fitness stats, you will want to guide the user through a process
to connect their fitness accounts. You will also want to provide layout configuration options for the user. 

The query will be also include a  `?&device-type=<device-type>` parameter. There is currently only
one device type, as described below in the `Device types` section.

### 2. Define a render url

On this url, you must serve a valid render for the device. 

On this url, the DEVICE authenticates with the same jason web token (JWT) that is also used for the login URL.
The JWT will contain your developer ID. Again, you must validate that the developer ID matches.

Additionally, the JWT  contains the `user_id`, `device_id` and `installation_id`.


The url will have the `device_type` in the query parameters. 
This means that you should be able to render an image on this url, for example
with setup instructions, even if the user has never visited the settings url before. 

### 3. Submit your app

Once you have the `settings url` and the `render url` ready, you can submit your app to us.
Users will then be able to install the app on their device by clicking on a
special installation link that you can place on your website. 




### Device types

| type string | description |
| ----------- | ----------- |
| `BLACK_AND_WHITE_SCREEN_800X480` | This device type requires you to render an 800x480 image. The image may be in color or greyscale, but it will be converted to black and white before being displayed on the screen. |
| `BLACK_AND_WHITE_SCREEN_960X640` | This device type requires you to render a 960x640 image. The image may be in color or greyscale, but it will be converted to black and white before being displayed on the screen. |


