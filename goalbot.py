import praw
import prawcore
import sqlite3
from time import sleep
from datetime import datetime

FOOTER = '''___\n\n
^^[About](https://redd.it/7kfrvj)
^^| ^^[Creator](https://reddit.com/u/MUFColin) 
^^| ^^[Feedback](/r/goalbot) 
^^| ^^[Donate](https://www.reddit.com/r/goalbot/wiki/donate)'''


def authenticate():
    print('Authenticating')
    reddit = praw.Reddit('goal_bot')
    print('Authenticated user {}'.format(reddit.user.me()))

    return reddit


def get_urls(sql_query, parameters):
    con = sqlite3.connect('bot.db')
    c = con.cursor()

    rows = c.execute(sql_query, tuple(parameters))

    reply = ''
    for row in rows:
        reply += '[{}: {} ({})](https://gfycat.com/{})'.format(row[5], row[6], row[7], row[0])
        for angle in range(1, 5):
            if row[angle]:
                reply += ', [Alt{}](https://gfycat.com/{})'.format(angle, row[angle])
        reply += '\n\n'

    if not reply:
        return ''

    reply += FOOTER
    return reply


def parse_body(body):
    start_index = body.find('!goalbot ')
    body = body[start_index + 9:]    # len('!goalbot ') == 9
    end_index = body.find('\n')

    if end_index != -1:
        body = body[:end_index]

    query = body.split(',')

    if len(query) < 2 and query[0].strip() != 'random':
        query = body.split(' ', 1)
        if len(query) > 1:
            return query

        return ''

    return query


def get_sql_items(user_query):
    if user_query[0].strip() == 'random':
        sql_query = '''SELECT GfyID, AltGfy1, AltGfy2, AltGfy3, AltGfy4, Player, Competition, Season
                    FROM Goals ORDER BY RANDOM() LIMIT 3;'''
        parameters = []

        return sql_query, parameters

    parameters = []

    sql_query = '''SELECT GfyID, AltGfy1, AltGfy2, AltGfy3, AltGfy4, Player, Competition, Season FROM Goals
                WHERE PlayerID=(SELECT PlayerID FROM Players
                WHERE ? COLLATE NOCASE IN (FullName, DistinctFirst, DistinctLast, AltName1, AltName2))'''

    player_name = user_query[0].strip()
    parameters.append(player_name)

    if 0 <= 1 < len(user_query):
        opponent = user_query[1].strip()

        sql_query += ''' AND MatchID IN (SELECT MatchID FROM Matches WHERE TeamID=(
                        SELECT TeamID FROM Teams WHERE ? COLLATE NOCASE IN (FullName, Acronym, ShortName1, ShortName2, ShortName3)))'''

        parameters.append(opponent)

    if 0 <= 2 < len(user_query):
        season = '%' + user_query[2].strip() + '%'
        sql_query += ' AND (Season LIKE ?)'
        parameters.append(season)

    sql_query += ';'

    return sql_query, parameters


def run_bot(reddit):
    print('Getting comments')

    for comment in reddit.subreddit('reddevils+mufcolin+goalbot').stream.comments():
        body = comment.body.lower()

        if '!goalbot ' in body:
            print('found comment: {}'.format(comment.permalink))

            with open('commented.txt', 'r') as outfile:
                seen_comments = outfile.read().splitlines()

            if comment.id not in seen_comments:
                try:
                    print('new comment')

                    user_query = parse_body(body)

                    if not user_query:
                        print('invalid user query')
                        continue

                    print('user query: {}'.format(user_query))

                    sql = get_sql_items(user_query)
                    sql_query = sql[0]
                    sql_parameters = sql[1]

                    reply = get_urls(sql_query, sql_parameters)

                except Exception as e:
                    print('error: {}'.format(e))

                else:
                    if reply:

                        try:
                            comment.reply(reply)
                            #print('reply made at {}'.format(str(datetime.now().time())))
                            print('reply made at {}'.format(datetime.now().strftime('%H:%M:%S %m/%d/%y')))

                            with open('commented.txt', 'a+') as outfile:
                                outfile.write(comment.id + '\n')

                            print('***********************')
                            sleep(20)

                        except praw.exceptions.APIException as api_exception:
                            print(api_exception)

                        except praw.exceptions.ClientException as client_exception:
                            print(client_exception)

                    else:
                        with open('non-working.txt', 'a+') as err_out:
                            try:
                                err_out.write('id: {}, query: {}\n'.format(comment.id, user_query))

                            except UnicodeEncodeError as unicode_error:
                                print(unicode_error)

                        print('no matching goals found')
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
            print('waiting 2 minutes')
            sleep(120)
            
            
if __name__ == '__main__':
    main()
