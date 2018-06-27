# -*- coding: utf-8 -*-

from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import datetime
import dateutil
from trello import TrelloClient

import sys, os, traceback, optparse, argparse
import time
import re
#from pexpect import run, spawn


calendarID = 'YOUR_CALENDAR_ID'

from oauth2client import tools
flags = tools.argparser.parse_args([]) 
# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = r'secret.json'
APPLICATION_NAME = 'Google Calendar API Python Trello sync'
BOARD = 'YOUR_BOARD'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'calendar-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        http = httplib2.Http(proxy_info = httplib2.proxy_info_from_environment(), disable_ssl_certificate_validation=True)
        if flags:
            credentials = tools.run_flow(flow, store, flags, http)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def main():
    client = TrelloClient(
        api_key='YOUR_SECRET',
        api_secret='YOUR_API_SECRET',
        token='YOUR_TOKEN',
        token_secret='YOUR_TOKEN_SECRET'
    )

    credentials = get_credentials()

    http = httplib2.Http(proxy_info = httplib2.proxy_info_from_environment(), disable_ssl_certificate_validation=True)
    auth = credentials.authorize(http)
    # http = credentials.authorize(httplib2.Http(), disable_ssl_certificate_validation=True)
    # http_auth = credentials.authorize(Http(proxy_info =     httplib2.ProxyInfo(httplib2.socks.PROXY_TYPE_HTTP_NO_TUNNEL, 'proxy url wihout     http://', 8080, proxy_user = '', proxy_pass = '') ))

    service = discovery.build('calendar', 'v3', http=http)
    # calendar_list = service.calendarList().list(pageToken=None).execute()
    # timeMin = datetime.datetime(2017, 10, 23, 2, 0).isoformat() + 'Z' # 'Z' indicates UTC time
    # timeMax = datetime.datetime(2017, 10, 25, 22, 0).isoformat() + 'Z' # 'Z' indicates UTC time
    tMin = dateutil.parser.parse(args[0], dayfirst=True)
    tMax = dateutil.parser.parse(args[1], dayfirst=True)
    # to include end of interval
    tMax += datetime.timedelta(days=1)
    print(tMin)
    print(tMax)
    timeMin = tMin.isoformat() + 'Z' # 'Z' indicates UTC time
    timeMax = tMax.isoformat() + 'Z' # 'Z' indicates UTC time


    eventsResult = service.events().list(
        calendarId=calendarID, timeMin=timeMin, timeMax=timeMax, singleEvents=True,
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])

    if not events:
        print('No events found.')
    for event in events:
        start = dateutil.parser.parse(event['start'].get('dateTime'))
        end = dateutil.parser.parse(event['end'].get('dateTime'))
        card = getTrelloCardByName(client, event['summary'])
        print(card)
        # print(float((end-start).seconds)/3600.0)
        addTaskTime(card, start, end)

def getTrelloCardByName(client, name):
    print(client.list_boards())
    boards = [board for board in client.list_boards() if board.name == BOARD]
    if len(boards) == 1:
        cards = boards[0].all_cards()
        return [card for card in cards if card.name==name][0]
    else:
        return None

def addTaskTime(card, start, end):
    # for now we update
    today = datetime.datetime.now().date()
    skew = today - start.date()
    print(skew.days)
    duration = (end-start).seconds/3600.0
    if skew.days > 0:
        text = "plus! -{2}d {0}/{1} ".format(duration, duration, skew.days)
    else:
        text = "plus! {0}/{1}".format(duration, duration)
    print(text)
    card.comment(text)

if __name__ == '__main__':
    try:
        start_time = time.time()

        usage = "usage: %prog [options] start end"
        parser = optparse.OptionParser(usage=usage)
        parser.add_option('-v', '--verbose', action='store_true', default=False, help='verbose output')

        (options, args) = parser.parse_args()
        print(args)
        if len(args) != 2:
            if len(args) == 0:
                args.append(str(datetime.datetime.now().date()))
                args.append(str(datetime.datetime.now().date()))
            else:
                parser.error('missing argument')
        if options.verbose: print(time.asctime())
        main()
        if options.verbose: print(time.asctime())
        if options.verbose: print('TOTAL TIME IN MINUTES:',)
        if options.verbose: print((time.time() - start_time) / 60.0)
        sys.exit(0)
    except KeyboardInterrupt as e: # Ctrl-C
        raise e
    except SystemExit as e: # sys.exit()
        raise e
    except Exception as e:
        print('ERROR, UNEXPECTED EXCEPTION')
        print(str(e))
        traceback.print_exc()
        os._exit(1)
