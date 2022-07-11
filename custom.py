import slack
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, Response, request
from slackeventsapi import SlackEventAdapter

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(
    os.environ['SIGNING_SECRET'], '/slack/events', app)

client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
BOT_ID = client.api_call("auth.test")['user_id']


def user_ping(user_id):
    ping_create = "<@" + user_id + ">"
    return ping_create

def channel_ping(channel_id):
    ping_create = "<#" + channel_id + ">"
    return ping_create

class HelpMessage:
    START_TEXT = {
        'type' : 'section',
        'text' : {
            'type' : 'mrkdwn',
            'text' : (
                '*Here is the help menu:* \n\n'
                ''
            )
        }
    }

    OPTION_TEXT = {
        'type' : 'section',
        'text' : {
            'type' : 'mrkdwn',
            'text' : (
                '`ticket` == Create a new ticket to Security team.\n'
                '`report` == How to submit a URL for takedown.)\n'
                '`app` == Application request or permission request.\n'
            )
        }
    }

    # REMEMBER_TEXT = {
    #     'type' : 'section',
    #     'text' : {
    #         'type' : 'mrkdwn',
    #         'text' : (
    #             '*Don\'t forget to @ me when you enter a command!* :parrot:'
    #         )
    #     }
    # }

    DIVIDER = {'type' : 'divider'}

    def __init__(self, channel, user):
        self.channel = channel
        self.user = user
        self.icon_emoji = ':robot_face:'
        self.timestamp = ''
        self.completed = False

    def get_message(self):
        return {
            'ts' : self.timestamp,
            'channel' : self.channel,
            'username' : 'Help Bot!',
            'icon_emoji' : self.icon_emoji,
            'blocks' : [
                self.START_TEXT,
                self.OPTION_TEXT,
                self.DIVIDER
            ]
        }

def extract_url(url_text):
        spl = url_text.split('\n')
        return spl

def send_help_message(channel, user):
    help = HelpMessage(channel, user)
    message = help.get_message()
    response = client.chat_postMessage(**message)
    help.timestamp = response['ts']



@app.route('/help', methods=['POST'])
def message_count():
    data = request.form
    user_id = data.get('user_id')
    channel_id = data.get('channel_id')
    send_help_message(channel_id, user_id)
    return Response(), 200

@app.route('/url', methods=['POST'])
def report_url():
    data = request.form
    url_text = data.get('text')
    user_id = data.get('user_id')
    ping = user_ping(user_id)
    channel_id = data.get('channel_id')
    url_list = extract_url(url_text)
    client.chat_postMessage(channel=channel_id, text=f"Thank you {ping} for reporting {url_text}")
    return Response(), 200



@slack_event_adapter.on('member_joined_channel')
def new_joiner(payload):
    event = payload.get('event', {})
    channel_id = event.get('channel')
    user_id = event.get('user')
    ping = user_ping(user_id)
    channel_tag = channel_ping(channel_id)
    client.chat_postMessage(channel=channel_id, text=f"Hi {ping},\nThank you for joining {channel_tag}!\nUse the `/help` command to see all options.")
    return Response(), 200


@slack_event_adapter.on('message')

def app_mention(payload):
    print(payload)
    event = payload.get('event', {})
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')

    if user_id != None and BOT_ID != user_id:
        match text:
            case 'ticket':
                return(client.chat_postMessage(channel=channel_id, text="Create a new ticket here: "))
            case 'report':
                return(client.chat_postMessage(channel=channel_id, text="Use the /url command in order to submit URLs for takedown.\nMake sure each URL is on a separate line."))
            case 'app':
                return(client.chat_postMessage(channel=channel_id, text="Request an application or permissions here: "))
            case _:
                return(client.chat_postMessage(channel=channel_id, text="Sorry, I didn't catch that."))



if __name__ == "__main__":
    app.run(debug=True, port=9696)