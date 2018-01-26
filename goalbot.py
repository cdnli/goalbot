import praw
import prawcore
import sqlite3
from time import sleep
from datetime import datetime

REPLY_FOOTER = '''___\n\n^^[About](https://redd.it/7kfrvj)
^^| ^^[Creator](https://reddit.com/u/MUFColin) ^^| ^^[Feedback](/r/goalbot) ^^| ^^[Donate](https://www.reddit.com/r/goalbot/wiki/donate)'''


def authenticate():
    print('Authenticating')
    reddit = praw.Reddit('goal_bot')
    print('Authenticated user {}'.format(reddit.user.me()))

    return reddit


def get_urls(query):
    query = query.split(',')

    if(len(query) < 2 and query[0].strip() != 'random'):
        return ''

    parameters = []

    sSQL = '''SELECT GfyID, AltGfy1, AltGfy2, AltGfy3, AltGfy4, Player, Competition, Season FROM Goals
            WHERE PlayerID=(SELECT PlayerID FROM Players
                            WHERE UPPER(?) IN (UPPER(DistinctFirst), UPPER(DistinctLast), UPPER(AltName1), UPPER(AltName2), UPPER(FullName)))'''
    
    player_name = query[0].strip()
    parameters.append(player_name)

    #if(query[1]):
    if 0 <= 1 < len(query):
        opponent = query[1].strip()
        sSQL += ''' AND MatchID IN (SELECT MatchID FROM Matches WHERE TeamID=(
            SELECT TeamID FROM Teams WHERE UPPER(?) IN (Acronym, UPPER(FullName), UPPER(ShortName1), UPPER(ShortName2), UPPER(ShortName3))))'''

        parameters.append(opponent)
        
    if 0 <= 2 < len(query):
        season = '%' + query[2].strip() + '%'
        sSQL += ' AND Season LIKE ?'
        parameters.append(season)
 
    sSQL += ';'

    if(query[0].strip() == 'random'):
        sSQL = '''select GfyID, AltGfy1, AltGfy2, AltGfy3,
                AltGfy4, Player, Competition, Season
                from goals order by random() limit 3;'''
        parameters = []

    con = sqlite3.connect('bot.db')
    c = con.cursor()
    
    rows = c.execute(sSQL, tuple(parameters))

    reply = ''
    for row in rows:
        #reply += '[{}: {}, {}](https://gfycat.com/{})\n\n'.format(row[1], row[2], row[3], row[0])
        reply += '[{}: {} ({})](https://gfycat.com/{})'.format(row[5], row[6], row[7], row[0])
        for angle in range(1,5):
            if(row[angle]):
                reply += ', [Alt{}](https://gfycat.com/{})'.format(angle, row[angle])
        reply += '\n\n'
        
    if not reply:
        return ''

    reply += REPLY_FOOTER
    return reply

def run_bot(reddit):
    print('Getting comments')

    for comment in reddit.subreddit('reddevils+mufcolin+goalbot').stream.comments():
        #match = re.findall('^!goalbot\s', comment.body)
        body = comment.body
        start_index = body.find('!goalbot ')

        if (start_index != -1):
            print('found comment: {}'.format(comment.permalink))

##            body = body[start_index:]
##            end_index = body.find('\n')
            
            with open('commented.txt', 'r') as outfile:
                seen_comments = outfile.read().splitlines()

            if comment.id not in seen_comments:
                try:
                    print('new comment')

                    body = body[start_index+9:] #len('!goalbot ') == 9
                    end_index = body.find('\n')
                    if end_index == -1:
                        query = body
                    else:
                        query = body[:end_index]
                    
                    print('query: {}'.format(query))
                    reply = get_urls(query)

                except Exception as e:  #fix
                    print(e)

                else:
                    if(reply != ''):
                        #print('reply: {}'.format(reply))
                        try:
                            comment.reply(reply)
                            print('reply made')

                            with open('commented.txt', 'a+') as outfile:
                                outfile.write(comment.id + '\n')

                            #print('waiting 20 seconds')
                            print(str(datetime.now().time()))
                            print('***********************')
                            sleep(20)
                            
                        except praw.exceptions.APIException as api_exception:
                            print(api_exception)
                            
                    else:
                        with open('non-working.txt', 'a+') as errout:
                            try:
                                errout.write('id: {}, query: {}\n'.format(comment.id, query))
                            except UnicodeEncodeError as unicode_error:
                                print(unicode_error)
                        print('no matching ids found')
                        print('***********************')
            else:
                print('seen')


def main():
    reddit = authenticate()
    while True:
        try:
            run_bot(reddit)
        except prawcore.exceptions.ServerError as http_error:
            print(http_error)
            print('waiting 2 minutes')  #reduce server load
            sleep(120)
        except prawcore.exceptions.ResponseException as response_error:
            print(response_error)
            print('waiting 2 minutes')
            sleep(120)
        except Exception as e:
            print('error: {}'.format(e))

if __name__ == '__main__':
    main()
