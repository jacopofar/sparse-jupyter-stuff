# the files are generated this way:
# docker pull pataquets/telegram-cli
# docker rm tgdocker
# docker run --name tgdocker -it -v ~/tgdocker/:/root/.telegram-cli pataquets/telegram-cli -f --json --disable-colors >>complete_logs_$(date -u +"%Y-%m-%dT%H:%M:%SZ").json

# this produces a set of files with names like complete_logs_2017-07-28T09:42:43Z.json
# these files contain events in JSON, both messages (including the text), user-online and other events, all mixed with ANSI control characters

# This script read these logs and produces clean TSV files with the online status and the messages

import datetime
import json
import os

# parameters that could me moved to CLI arguments if needed
messages_file = open('messages.tsv', 'w', encoding='utf8')
online_presence_file = open('online.tsv', 'w', encoding='utf8')
tg_cli_logs_folder = '/Users/jfarina/Documents/my/tgdocker'


messages_file.write('user_id\tuser_print_name\tto_id\tto_print_name\ttimestamp\ttext\n')
messages_file.write('user_id\tuser_print_name\ttimestamp\n')

for logfile_path in [f.path for f in os.scandir(tg_cli_logs_folder) if f.is_file() and f.name.startswith('complete_logs_')]:
    print(logfile_path)
    with open(logfile_path, 'r', encoding='utf-8') as logfile:
        for linenum, line in enumerate(logfile):
            line_without_ansi = line[line.find('{"'): -1]
            if len(line_without_ansi) < 10:
                continue
            obj = json.loads(line_without_ansi.encode('utf8'))
            if 'text' in obj:
                messages_file.write('\t'.join([
                    str(obj['from']['peer_id']),
                    obj['from']['print_name'],
                    str(obj['to']['peer_id']),
                    obj['to']['print_name'],
                    str(datetime.datetime.utcfromtimestamp(int(obj['date'])).isoformat()),
                    obj['text'],
                    '\n'
                ]))
                continue

            if 'event' in obj and obj['event'] == 'read':
                online_presence_file.write('\t'.join([
                    str(obj['from']['peer_id']),
                    obj['from']['print_name'],
                    str(datetime.datetime.utcfromtimestamp(int(obj['date'])).isoformat()),
                    '\n'
                ]))
                continue
            # a message but has no text (that's it, multimedia), is ignored
            if obj['event'] == 'message':
                continue
            if 'event' in obj and obj['event'] == 'online-status' and obj['online']:
                online_presence_file.write('\t'.join([
                    str(obj['user']['peer_id']),
                    obj['user']['print_name'],
                    # for some reason, tg-cli uses two different date formats for messages/reads and online statuses
                    # so ugly :(
                    obj['when'].replace(' ', 'T'),
                    '\n'
                ]))
                continue