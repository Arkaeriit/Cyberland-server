# Cyberland

![Cyberland logo](https://cyberland.bobignou.red/static/ibmhq.png)

## What is Cyberland

Cyberland is a textboard that offers no frontend. Most of the time, the user makes their own front end. The protocol, as far as I know, made by Github user Jorde Kang and the original repo is [here](https://github.com/jorde-s-kang/cyberland). An alternative version of the server has also been made [here](https://github.com/cyberland-digital/cyberland/wiki).

Unfortunately, the servers hosting the originals Cyberland have been taken down. Thus, I want to make a new one. I have chosen to make it from scratch instead of reusing one for two reasons. Firstly, I want to learn a bit about web technologies. Secondly, as the specifications of the Cyberland protocol have never been written, I want to make them.

## Using cyberland

### Server
I am hosting this server at [cyberland.bobignou.red](https://cyberland.bobignou.red). Check it out.

### Client
To access the Cyberland server, you need a client. You can find plenty of them if you search for "cyberland client" on Github but I can always advertise [mine](https://github.com/Arkaeriit/cyberland.lua).

On the other hand, if you want to use Cyberland the way it is intended, you should try to write your own client.

## This server

### Launching it
This Cyberland server is written in Python 3 using Flask. Running `cyberland.py` will launch it on port 8901. It's then up to you to route the internet traffic to it.

### Configuration
The server is configurated from a single JSON file. The JSON file contains an array where each entry corresponds to a board the server will serve.
For each board, the configuration fields are the following:
| Name                     | type    | Description                                                                                                |
|--------------------------|---------|------------------------------------------------------------------------------------------------------------|
| name                     | string  | Name of the board as used in the URL.                                                                      |
| long\_name               | string  | Full name of the board (optional).                                                                         |
| description              | string  | A description of what this board is about.                                                                 |
| max\_post\_size          | integer | Maximum size of a post in bytes.                                                                           |
| enable\_ansi\_code       | boolean | Set to true to enable ANSI escape codes in a board.                                                        |
| max\_replies\_thread     | integer | Maximum number of posts the server can present when the parameter `thread` is set. Set to 0 to disable.    |
| max\_replies\_no\_thread | integer | Maximum number of posts the server can present when the parameter `thread` is not set. Set to 0 to disable.|

I included in this repository the configuration used on `cyberland;github.com`.

### Database
As of now, the serer does not uses a proper database. All the posts are stored in a JSON file.

### Default pages
This server also present some web pages that are not Cyberland boards. They are the following:
* A welcome page at the root.
* Configuration page: at `<server URL>/config/`.
* At `<server URL>/status`, there is a list of all board and the number of posts in each board.
* A very basic tutorial at `<server URL>/tut.txt`
* A small descriptions of boards at `<server URL>/boards`.
* A nice ASCII banner at `<server URL>/banner.txt`.

### Logging and banning
This server generate a line of log for each new message. For every new message, a new line will be added on the log file `cyberland_log`. The line contains a hash of the IP of the poster, the board where the post have been made and the ID of the post.

In order to bans some peoples from the server, you simply have to write the hash of their IP to a JSON array in the file `bans.json`. This file is optional, if it is not found, an error will be printed at the startup of the server but the server will run nonetheless.

### Anti-spam
To prevent users from spamming, there is a delay between each post one user can do. The user is tracked with its IP. Furthermore, to prevent users from bypassing the delay, they must wait some time before their first connection. All the constants related to this are at the beginning of `anti_spam.py`.

To make sure that trusted users will not have to wait for the delay, you can put their hashed IPs in a list in the file `verified.json`.

### Content filter
This server also provides some optional content filters. You can write an array of forbidden words in `bad_words.js` and the server will not accept any message containing those words.

## Cyberland protocol

### Boards
A Cyberland server hosts multiple boards. Each board is independent of the other and they are meant to be about various subjects. For example, the board `/t/` form `cyberland.bobignou.red` is meant to be about technology while the board `/n/` is meant to be about news.

### Post
Cyberland posts are very simples. They have a unique `id` field which is a positive integer. This field corresponds to the order in the board they are posted. The first post on a board will have id 1, the second will have id 2. Two posts on the same board can not have the same id but two posts from two different boards can have the same id.

The posts also have a `ReplyTo` field. This field contains a positive integer that is the id of another post from the same board. If that field contains 0, that means that the post is not replying to any other and is the start of a new thread. Alternatively, the field can contain "null" to express the same thing.

Then, the posts have a `time` fields. This field should either contain the time-stamp of the post in UNIX seconds at UTC or 0 if this is not applicable or not computed.

Lastly, the post has a `content` field that contains the message in the post. The message can be made from Unicode characters or, if the board allows it, Unicode characters and ANSI escape code. The content field can have a maximum size and the server could reject messages that are bigger than this size.

### Communication
A Cyberland server presents a REST API to the rest to let the client post and read messages.

A Cyberland server should have more than one board. The board is selected in the URL of the request. For example, to interact with the board /t/ of the server `cyberland.bobignou.red`, you should make requests to `cyberland.bobignou.red/t/`.

The operation to do is selected with the HTTP method used and the details of the operation are selected in the parameters of the request.

The server replies with JSON data or HTTP error codes.

#### Posting messages
Posting a message on a board is made with the POST HTTP method. The message and other info are in the form of the request. The form should be an URL encoded data form. The field `content` contains the message and the optional field `replyTo` can contain the id of a post we want to reply to.

If the form is valid, the server will reply with the code 200. If it is not, it will reply with the code 400 and with a message explaining what is wrong.

#### Reading posts
Reading what is on a board is made with the GET HTTP method. The request is specified with the parameters in the URL of the request. 

The first valid parameter is `num`. It should contain a positive integer. It describes the maximum number of posts the server should send. If it is not specified, the server will send the maximum number of posts that are compliant with the rest of the request.

The second valid parameter is `thread`. It should contain an id. If it is set, the server will return the post with the given id and posts replying to it.

The server will reply with a JSON array containing all the posts requested. If the parameter `thread` is not set, the post with the greatest id will be at the index 0 of the array. The rest of the posts are sorted by decreasing id. If the parameter `thread` is set, the post with the smaller id will be at index 0 and the other post will be sorted by increasing id. This is made that way to ensure that a request with parameters `num=1` and thread not set will return the latest post and a request where `num=1&thread=<XX>` will return the pos with id `<XX>`.

If the parameter makes sense, the server will reply with the status code 200. If there is an error the status code 400 will be replied and an error message will be sent.

To prevent clients from making too many requests, the server reserve itself the right to capping the maximum number of post to be sent. If the number is capped in a reply, it is up to the client to check for an error. I really advise against doing so when the `thread` field is set to ensure that users can read all threads completely.

### Default pages
A Cyberland server must provides some default pages to help both the client makers and users to use the server.

#### tut.txt
At `<banner URL>/tut.txt` there should be a swift tutorial as a raw text file.

#### boards
At `<server URL>/boards` there should be a JSON list of all the boards. For each board, there is a dictionary with the following fields:
* `slug` - the fully qualified path of the board /\*/, eg: /t/
* `name` - the long name of the board, eg: tech
* `charLimit` - the character limit per post on the board
* `posts` - the total number of posts to the board at the time of the request

#### banner.txt
At `<server URL>/banner.txt` there should be a nice ASCII art that can act as the banner for the server.

## Differences with the old Cyberland protocol
With the old Cyberland servers, an [other specification](https://github.com/cyberland-digital/cyberland-protocol/blob/master/protocol.md) had been written. I choose to modify some part of the specification that I did not find well thought out and that were not critical for the clients.

### Root in plain text
To make the site more friendly, I choose to make the root page in HTML. Thanks to that, I can add link and picture in this page.

Unfortunately, this also means that the root page is not suitable for the ASCII banner. I choose to create a new static page, `/banner.txt` where the ASCII banner is located.

### Error code
The original specification mention the use of different HTTP return code to detail the errors. But as there is more kind of errors than what the HTTP return code are made for. Thus, I believe that it make more sense to detail the error in a text message. In that situation, the various code don't make much sense anymore and using the 400 code all the time is enough.

### Time
The original specification mention that the time should be returned in the format "YYYY-MM-DD hh:mm:ss". But I feel like it makes more sense to return the time in UNIX seconds and let the client handle the conversion.

### TODO
There is some parts of the original specification that I want to implement but that I did not implemented yer:
* Bump count
* offset parameter

