import praw
import sqlite3
import time

REPLY_FOOTER = '''___\n\n^^[About](https://redd.it/7kfrvj)
^^| ^^[Creator](https://reddit.com/u/MUFColin)/[Twitter](https://twitter.com/MUFColin) ^^| ^^[Feedback](/r/goalbot)'''

def authenticate():
    print('Authenticating')
    reddit = praw.Reddit('goal_bot')
    print('Authenticated user {}'.format(reddit.user.me()))

    return reddit

def get_urls(query):
    query = query.split(',')

    if(len(query) < 2):
        return ''
    
    parameters = []

    sSQL = '''SELECT GfyID, AltGfy1, AltGfy2, AltGfy3, AltGfy4, Player, Competition, Season FROM Goals
            WHERE PlayerID=(SELECT PlayerID FROM Players
                            WHERE UPPER(?) IN (UPPER(DistinctFirst), UPPER(DistinctLast), UPPER(AltName1), UPPER(AltName2), UPPER(FullName)))'''
    
    player_name = query[0].strip()
    parameters.append(player_name)


    if(query[1]):
        opponent = query[1].strip()
        sSQL += ''' AND MatchID IN (SELECT MatchID FROM Matches WHERE TeamID=(
            SELECT TeamID FROM Teams WHERE UPPER(?) IN (Acronym, UPPER(FullName), UPPER(ShortName1), UPPER(ShortName2), UPPER(ShortName3))))'''

##        if(opponent.isupper()):
##            sSQL += 'Acronym=?)'
##        else:
##            sSQL += 'UPPER(?) IN (UPPER(FullName), UPPER(ShortName1), UPPER(ShortName2), UPPER(ShortName3)))'
        parameters.append(opponent)
        
    if 0 <= 2 < len(query):
        season = '%' + query[2].strip() + '%'
        sSQL += ' AND Season LIKE ?'
        parameters.append(season)
    
    sSQL += ';'
    
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
        start_index = comment.body.find('!goalbot ')

        if (start_index != -1):
            print('found comment id: {}'.format(comment.id))

            with open('commented.txt', 'r') as outfile:
                seen_comments = outfile.read().splitlines()

            if comment.id not in seen_comments:
                try:
                    print('new comment')
                    query = comment.body[start_index + 9:]    #len('!goalbot ') == 9
                    print('query: {}'.format(query))
                    reply = get_urls(query)

                except Exception as e:  #fix
                    print(e)

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

def main():
    reddit = authenticate()
    while True:
        run_bot(reddit)

if __name__ == '__main__':
    main()