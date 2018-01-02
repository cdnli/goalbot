import praw
import re
import time
import sqlite3

REPLY_FOOTER = '''___\n\n^^[About](https://redd.it/7kfrvj)
^^| ^^[Creator](https://reddit.com/u/MUFColin)/[Twitter](https://twitter.com/MUFColin) ^^| ^^[Feedback](/r/goalbot)'''

def authenticate():
    print('Authenticating')
    reddit = praw.Reddit('goal_bot')
    print('Authenticated user {}'.format(reddit.user.me()))

    return reddit


def get_urls(query):
    query = query.split(',')

    parameters = []
    #sSQL = 'SELECT GfyID, Player, Competition, Season FROM Goals WHERE PlayerID=(SELECT PlayerID FROM Players WHERE FullName LIKE ?)'
    sSQL = 'SELECT GfyID, Player, Competition, Season FROM Goals WHERE PlayerID=(SELECT PlayerID FROM Players WHERE '

    player_name = query[0].strip()

    #x = player_name.split(' ')
    # if(len(x) > 1):
    #     first_name = x[0]
    #     last_name = ' '.join(x[1:])
        #sSQL += ('First LIKE ? AND Last LIKE ?')
    sSQL += 'UPPER(?) IN (UPPER(DistinctFirst), UPPER(DistinctLast), UPPER(AltName1), UPPER(AltName2), UPPER(FullName)))'
    parameters.append(player_name)


    if(query[1]):
        opponent = query[1].strip()
        sSQL += ' AND MatchID IN (SELECT MatchID FROM Matches WHERE TeamID=(SELECT TeamID FROM Teams WHERE '

        if(opponent.isupper()):
            sSQL += 'Acronym=?)'
        else:
            sSQL += 'UPPER(?) IN (UPPER(FullName), UPPER(ShortName1), UPPER(ShortName2), UPPER(ShortName3)))'
        parameters.append(opponent)

    # if(query[2]):
    #     comp = query[2]
    #     sSQL += ' AND Competition=(SELECT actual_name from Competitions. . . '
    # if (query[3]):
    #     comp = query[2]
    #     sSQL += ' '

    sSQL += ');'
    con = sqlite3.connect('bot.db')
    c = con.cursor()
    #print('sql: {}'.format(sSQL))
    ids = c.execute(sSQL, tuple(parameters))

    reply = ''
    for row in ids:
        reply += '[{}: {}, {}](https://gfycat.com/{})\n\n'.format(row[1], row[2], row[3], row[0])

    if not reply:
        return ''

    reply += REPLY_FOOTER
    return reply

def run_bot(reddit):
    print('Getting comments')

    #for comment in reddit.subreddit('mufcolin').comments(limit = 10):
    for comment in reddit.subreddit('reddevils+mufcolin+goalbot').stream.comments():
        #match = re.findall('^!goalbot\s', comment.body)
        start_index = comment.body.find('!goalbot ')

        if (start_index != -1):
            print('found comment id: {}'.format(comment.id))

            with open('commented.txt', 'r') as outfile:
                seen_comments = outfile.read().splitlines()

            if comment.id not in seen_comments:
                try:
                    print('new comment')
                    #lookup in sqlite
                    query = comment.body[start_index + 9:]    #len('!goalbot ') == 9
                    print('query: {}'.format(query))
                    reply = get_urls(query)

                except Exception as e:
                    print(e)
                    #print('failed for some reason') #fix

                else:
                    if(reply != ''):
                        
                            
                        print('reply: {}'.format(reply))
                        comment.reply(reply)
                        print('reply made')

                        with open('commented.txt', 'a+') as outfile:
                            outfile.write(comment.id + '\n')

                        print('waiting 20 seconds')
                        time.sleep(20)
                        
                    else:
                        with open('non-working.txt', 'a+') as errout:
                            errout.write('id: {}, query: {}\n'.format(comment.id, query))
                        print('no matching ids found')
            else:
                print('seen')
        # print('waiting 20 seconds')
        # time.sleep(20)

    print('waiting 30 seconds')
    time.sleep(30)

def main():
    reddit = authenticate()
    while True:
        run_bot(reddit)

if __name__ == '__main__':
    main()
