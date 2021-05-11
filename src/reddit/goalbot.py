import praw
import prawcore
import sqlite3
from time import sleep
from datetime import datetime

FOOTER = '''___\n\n
^^[About](https://redd.it/7kfrvj)
^^| ^^[Feedback/Test](/r/goalbot) 
^^| ^^[Donate](https://www.reddit.com/r/goalbot/wiki/donate)'''


def authenticate():
    print('Authenticating')
    reddit = praw.Reddit('goal_bot')
    print('Authenticated /u/{}'.format(reddit.user.me()))

    return reddit


def run_bot(reddit):
    print('Fetching 100 recent comments')

    subreddits = '+'.join(['reddevils', 'goalbot', 'goalbottest'])
    #subreddits = 'goalbottest'

    for comment in reddit.subreddit(subreddits).stream.comments():
        body = comment.body.lower()

        if '!goalbot ' in body or '!matchbot ' in body or '!assistbot ' in body:
            if not new_comment(comment.id):
                print('seen')
                continue

            if '!goalbot ' in body:
                print('found goal comment: {}'.format(comment.permalink))
                parsed_comment = parse_comment(body, 'goal')
                query = build_goal_query(parsed_comment)

            elif '!matchbot ' in body:
                print('found match comment: {}'.format(comment.permalink))
                parsed_comment = parse_comment(body, 'match')
                query = build_match_query(parsed_comment)

            elif '!assistbot ' in body:
                print('found assist comment: {}'.format(comment.permalink))
                parsed_comment = parse_comment(body, 'assist')
                query = build_assist_query(parsed_comment)

            #maybe split up into build_reply & make_reply
            reply(comment, query, parsed_comment)


def new_comment(id):
    query = 'SELECT id FROM Commented WHERE id = ?;'

    con = sqlite3.connect('bottest.db')
    c = con.cursor()

    row = c.execute(query, (id,)).fetchone()

    return row is None


def parse_comment(body, comment_type):
    if comment_type == 'goal':
        start_index = body.find('!goalbot ')
        body = body[start_index + len('!goalbot '):]
    elif comment_type == 'match':
        start_index = body.find('!matchbot ')
        body = body[start_index + len('!matchbot '):]
    elif comment_type == 'assist':
        start_index = body.find('!assistbot ')
        body = body[start_index + len('!assistbot '):]

    end_index = body.find('\n')

    if end_index != -1:
        body = body[:end_index]


    query = body.split(',')

    if query[0] == 'random':
        return ['random']

    if len(query) < 2:
        # if user forgot comma, split on first space
        query = body.split(' ', 1)

        if len(query) < 2:
            return []
    
    query = list(map(str.strip, query))

    #for 'season' search for LIKE operator in sql
    # todo fix
    if comment_type == 'goal' and len(query) > 2 and query[2]:
        #query[2] = '%{}%'.format(query[2])
        query[2] = parse_season(query[2])
    elif comment_type == 'match':
        #query[1] = '%{}%'.format(query[1])
        query[1] = parse_season(query[1])

        #first character of home/away
        if len(query) > 2 and len(query[2]) > 1:
            query[2] = query[2][0]

    elif comment_type == 'assist' and len(query) > 2 and query[2]:
        query[2] = parse_season(query[2])

    return query


def parse_season(season):
    if season.find('-') != -1:
        season = season.split('-')
    else:
        season = season.split('/')

    season_count = len(season)

    if season_count == 1:
        season = season[0][-2:]
    elif season_count == 2:
        season = '-'.join([season[0][-2:], season[1][-2:]])

    return '%{}%'.format(season)


def build_goal_query(user_query):
    user_query_length = len(user_query) #todo fix naming(?)

    if user_query_length == 0:
        return ''

    if user_query[0] == 'random':
        return '''
            SELECT GfyID, AltGfy1, AltGfy2, AltGfy3, AltGfy4,
                p.FullName,
                m.Competition, m.Season, m.MatchID, m.Opponent, m.MatchDate, m.GoalsFor, m.GoalsAgainst, g.minute,
                m.Location, g.IsPen, g.IsOwnGoal
            FROM Goals g
            INNER JOIN Matches m ON m.MatchID = g.MatchID
            INNER JOIN Players p ON p.PlayerID = g.PlayerID
            ORDER BY RANDOM() LIMIT 3;
        '''

    sql_query = '''
        SELECT GfyID, AltGfy1, AltGfy2, AltGfy3, AltGfy4,
                p.FullName,
                m.Competition, m.Season, m.MatchID, m.Opponent, m.MatchDate, m.GoalsFor, m.GoalsAgainst, g.minute,
                m.Location, g.IsPen, g.IsOwnGoal
        FROM Goals g
        INNER JOIN Matches m ON m.MatchID = g.MatchID
        INNER JOIN Players p ON p.PlayerID = g.PlayerID
        WHERE p.PlayerID=(
            SELECT PlayerID 
            FROM Players
            WHERE ? COLLATE NOCASE IN (FullName, DistinctFirst, DistinctLast, AltName1, AltName2)
        )
    '''

    sql_query += '''
    AND m.MatchID IN (
        SELECT MatchID FROM Matches WHERE TeamID=(
            SELECT TeamID FROM Teams WHERE ? COLLATE NOCASE IN (
                FullName, Acronym, ShortName1, ShortName2, ShortName3
            )
        )
    '''

    # season
    if user_query_length > 2:
        sql_query += ' AND (Season LIKE ?)'

    sql_query += ') ORDER BY GoalDate, CAST(GoalNum AS INTEGER);'    # todo update type in sql(?)

    return sql_query


def build_match_query(user_query):
    user_query_length = len(user_query)  # todo fix naming(?)

    if user_query_length == 0:
        return ''

    if user_query[0] == 'random':
        return '''
            SELECT GfyID, AltGfy1, AltGfy2, AltGfy3, AltGfy4,
                p.FullName,
                m.Competition, m.Season, m.MatchID, m.Opponent, m.MatchDate, m.GoalsFor, m.GoalsAgainst, g.minute,
                m.Location, g.IsPen, g.IsOwnGoal
            FROM Goals g
            INNER JOIN Matches m ON m.MatchID = g.MatchID
            INNER JOIN Players p ON p.PlayerID = g.PlayerID
            WHERE g.MatchID=(
                SELECT MatchID
                FROM Matches
                WHERE GoalsFor > 0
                ORDER BY RANDOM() LIMIT 1
            );
        '''

    sql_query = '''
        SELECT GfyID, AltGfy1, AltGfy2, AltGfy3, AltGfy4,
                p.FullName,
                m.Competition, m.Season, m.MatchID, m.Opponent, m.MatchDate, m.GoalsFor, m.GoalsAgainst, g.minute,
                m.Location, g.IsPen, g.IsOwnGoal
        FROM Goals g
        INNER JOIN Matches m ON m.MatchID = g.MatchID
        INNER JOIN Players p ON p.PlayerID = g.PlayerID
        WHERE m.MatchID IN (
            SELECT MatchID FROM Matches
            WHERE TeamID=(
                SELECT TeamID
                FROM Teams
                WHERE ? COLLATE NOCASE IN (FullName, Acronym, ShortName1, ShortName2, ShortName3)
            ) 
            AND Season LIKE ?'''

    if user_query_length > 2 and user_query[2]:
        sql_query += ' AND Location like ?'

    sql_query += ''')
        ORDER BY g.GoalDate, CAST(g.GoalNum AS INTEGER);
    '''

    return sql_query


def build_assist_query(user_query):
    user_query_length = len(user_query)  # todo fix naming(?)

    if user_query_length == 0:
        return ''

    # if user_query[0] == 'random':
    #   pass

    sql_query = '''
        SELECT GfyID, AltGfy1, AltGfy2, AltGfy3, AltGfy4,
                p.FullName,
                m.Competition, m.Season, m.MatchID, m.Opponent, m.MatchDate, m.GoalsFor, m.GoalsAgainst, g.minute,
                m.Location, g.IsPen, g.IsOwnGoal
        FROM Goals g
        inner join players p on p.playerid = g.playerid
        inner join matches m on m.matchid = g.matchid
        where (assistplayerid = (
            SELECT PlayerID 
            FROM Players
            WHERE ? COLLATE NOCASE IN (FullName, DistinctFirst, DistinctLast, AltName1, AltName2)
        ) and g.playerid = (
            SELECT PlayerID 
            FROM Players
            WHERE ? COLLATE NOCASE IN (FullName, DistinctFirst, DistinctLast, AltName1, AltName2)
        ))
    '''

    if user_query_length > 2:
        sql_query += ' and m.Season LIKE ?'

    sql_query += ' ORDER BY g.GoalDate, CAST(g.GoalNum AS INTEGER);'

    return sql_query


def reply(comment, query, parameters):
    if parameters == ['random']:
        parameters = []

    con = sqlite3.connect('bottest.db')
    c = con.cursor()

    rows = c.execute(query, tuple(parameters))

    reply = ''
    current_match_id = ''
    goal_count = 1
    referenced_gfys = []

    for row in rows:
        gfy_ids = [row[0], row[1], row[2], row[3], row[4]]
        full_name = row[5]
        competition = row[6]
        season = "'" + row[7]
        match_id = row[8]
        opponent = row[9]

        match_date = row[10]
        goals_for = row[11]
        goals_against = row[12]
        minute = row[13]
        location = row[14]
        is_pen = row[15]
        is_og = row[16]
        pen_or_og = ''

        if current_match_id != match_id:
            if current_match_id != '':
                #reply += '\n\n&nbsp;\n\n'
                reply += '\n\n'


            first_team = 'Man Utd'
            second_team = opponent

            # keep home team first if possible
            # todo fix logic
            if location == 'A':
                first_team = opponent
                second_team = 'Man Utd'
                x = goals_for
                goals_for = goals_against
                goals_against = x
#                first_team, second_team = second_team, first_team

            # todo update to 3.6(?) to get the python equivalent of js template literals
            # ex. Man Utd 8-2 Arsenal (Premier League) 28 August 2011
            reply += '**{} {}-{} {} ({}) {}**\n\n'.format(first_team, goals_for, goals_against, second_team,
                                                               competition, season)
            current_match_id = match_id
            #goal_count = 1  # todo(ne) eventually replace with minute of goal in match (if available)

        # todo simplify (need to convert from None) & move above
        if minute:
            minute = " '" + minute
        else:
            minute = ''

        if is_pen:
            #pen_or_og = ' (pen)'
            pen_or_og = ''
        elif is_og:
            # player name is still 'Own Goal', but I could insert opposition player soon
            pen_or_og = ''

        reply += '[{}{}{}](https://gfycat.com/{})'.format(full_name, pen_or_og, minute, gfy_ids[0])


        for angle in range(1, len(gfy_ids)):
            if gfy_ids[angle]:
                reply += ', [Alt{}](https://gfycat.com/{})'.format(angle, gfy_ids[angle])

        goal_count += 1
        reply += '\n\n'

        referenced_gfys.append(gfy_ids[0])

    if reply == '':
        #todo log invalid query somewhere
        print('no matching goals found')
        print('***********************')
        #pass
        log_seen_comment(comment)
        return

    reply += FOOTER

    try:
        comment.reply(reply)
        #maybe log this in sql too
        print('reply made at {}'.format(datetime.now().strftime('%H:%M:%S %m/%d/%y')))

        print('***********************')
        #sleep(20)   #todo re-read api limitations

    except praw.exceptions.APIException as api_exception:
        print(api_exception)
        return

    except praw.exceptions.ClientException as client_exception:
        print(client_exception)
        return



    log_seen_comment(comment)
    increment_referenced_goals_count(referenced_gfys)



def log_seen_comment(comment):
    con = sqlite3.connect('bottest.db')
    c = con.cursor()

    query = 'INSERT INTO Commented (id, username) VALUES (?, ?);'

    parameters = [comment.id, comment.author.name]

    c.execute(query, tuple(parameters))
    con.commit()


def increment_referenced_goals_count(gfy_ids):
    #gfy_ids = list(filter(None, gfy_ids))

    query = 'UPDATE Goals SET [Count] = [Count] + 1 WHERE GfyID IN ("{}")'.format('", "'.join(gfy_ids))
    #print(query)

    con = sqlite3.connect('bottest.db')
    c = con.cursor()
    c.execute(query)
    con.commit()


if __name__ == '__main__':
    reddit = authenticate()

    while True:
        try:
            run_bot(reddit)

        except prawcore.exceptions.ServerError as http_error:
            print(http_error)
            print('waiting 2 minutes')  # reduce server load
            sleep(120)

        except prawcore.exceptions.ResponseException as response_error:
            print(response_error)
            print('waiting 2 minutes')
            sleep(120)

        except Exception as e:
            print('error: {}'.format(e))
            print('waiting 5 minutes')  #likely internet issue
            sleep(300)

        finally:
            print('retrying')
