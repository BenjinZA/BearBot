import aiosqlite
import time


# create DB
async def create_db():
    async with aiosqlite.connect('fantasyDB/fantasy.db') as db:
        create_matches = '''
                            CREATE TABLE matches
                            (
                                match_id        text,
                                league_name     text,
                                radiant_team    text,
                                dire_team       text,
                                start_time      real,
                                allow_bets      integer,
                                radiant_win     integer,
                                unfinished      integer
                            )'''
        await db.execute(create_matches)
        await db.commit()

        create_messages = '''
                            CREATE TABLE messages
                            (
                                bot_id          text,
                                match_id        text,
                                channel_id      text,
                                message_id      text
                            )'''

        await db.execute(create_messages)
        await db.commit()

        create_channels = '''
                            CREATE TABLE channels
                            (
                                bot_id          text,
                                channel_id      text
                            )'''

        await db.execute(create_channels)
        await db.commit()

        create_balances = '''
                            CREATE TABLE balances
                            (
                                user_id         text,
                                balance         integer
                            )'''

        await db.execute(create_balances)
        await db.commit()

        create_bets = '''
                            CREATE TABLE bets
                            (
                                match_id        text,
                                user_id         text,
                                radiant_bet     integer,
                                dire_bet        integer
                            )'''

        await db.execute(create_bets)
        await db.commit()
        await db.close()


# channel functions
async def check_channel(bot_id, channel_id):
    async with aiosqlite.connect('fantasyDB/fantasy.db') as db:
        check_channel_text = '''
                                SELECT
                                    channel_id
                                FROM
                                    channels
                                WHERE bot_id = '%s' AND channel_id = '%s' ''' % (bot_id, channel_id)

        result = await db.execute(check_channel_text)
        channel = await result.fetchone()
        await db.close()
        if channel:
            return channel[0]
        else:
            return None


async def get_channels(bot_id):
    async with aiosqlite.connect('fantasyDB/fantasy.db') as db:
        check_channel_text = '''
                                SELECT
                                    channel_id
                                FROM
                                    channels
                                WHERE bot_id = '%s' ''' % bot_id

        result = await db.execute(check_channel_text)
        channels = []
        async for row in result:
            channels.append(row[0])

        await db.close()

        return channels


async def add_channel(bot_id, channel_id):
    async with aiosqlite.connect('fantasyDB/fantasy.db') as db:
        add_channel_text = '''
                            INSERT INTO channels
                            (
                                bot_id,
                                channel_id
                            )
                            VALUES
                            (
                                '%s',
                                '%s'
                            )''' % (bot_id, channel_id)

        await db.execute(add_channel_text)
        await db.commit()
        await db.close()


async def remove_channel(bot_id, channel_id):
    async with aiosqlite.connect('fantasyDB/fantasy.db') as db:
        remove_channel_text = '''
                                DELETE FROM channels
                                WHERE bot_id = '%s' AND channel_id = '%s' ''' % (bot_id, channel_id)

        await db.execute(remove_channel_text)
        await db.commit()


# match functions
async def get_matches(get_type):
    async with aiosqlite.connect('fantasyDB/fantasy.db') as db:
        get_matches_text = '''
                            SELECT
                                match_id,
                                league_name,
                                radiant_team,
                                dire_team,
                                start_time,
                                allow_bets,
                                radiant_win,
                                unfinished
                            FROM
                                matches
                            WHERE radiant_win IS NULL AND unfinished IS NULL'''

        result = await db.execute(get_matches_text)

        matches = []
        async for row in result:
            if get_type == 'info':
                matches.append({'league_name': row[1], 'match_id': row[0], 'radiant_team': row[2], 'dire_team': row[3]})
            elif get_type == 'full':
                matches.append({'league_name': row[1], 'match_id': row[0], 'radiant_team': row[2], 'dire_team': row[3], 'start_time': row[4], 'allow_bets': row[5], 'radiant_win': row[6], 'unfinished': row[7]})

        await db.close()

        return matches


async def get_bet_matches():
    async with aiosqlite.connect('fantasyDB/fantasy.db') as db:
        get_matches_text = '''
                            SELECT
                                match_id,
                                league_name,
                                radiant_team,
                                dire_team,
                                start_time,
                                allow_bets,
                                radiant_win,
                                unfinished
                            FROM
                                matches
                            WHERE radiant_win IS NULL AND unfinished IS NULL AND allow_bets = 1'''

        result = await db.execute(get_matches_text)

        matches = []
        async for row in result:
            matches.append({'league_name': row[1], 'match_id': row[0], 'radiant_team': row[2], 'dire_team': row[3], 'start_time': row[4], 'allow_bets': row[5], 'radiant_win': row[6], 'unfinished': row[7]})

        await db.close()

        return matches


async def add_match(match):
    async with aiosqlite.connect('fantasyDB/fantasy.db') as db:
        add_match_text = '''
                            INSERT INTO matches
                            (
                                match_id,
                                league_name,
                                radiant_team,
                                dire_team,
                                start_time,
                                allow_bets
                            )
                            VALUES
                            (
                                '%s',
                                '%s',
                                '%s',
                                '%s',
                                %f,
                                %d
                            )''' % (match['match_id'], match['league_name'], match['radiant_team'], match['dire_team'], time.time(), 1)
        await db.execute(add_match_text)
        await db.commit()
        await db.close()


async def disallow_bet(match_id):
    async with aiosqlite.connect('fantasyDB/fantasy.db') as db:
        disallow_bet_text = '''
                            UPDATE matches
                            SET allow_bets = 0
                            WHERE match_id = '%s' ''' % match_id

        await db.execute(disallow_bet_text)
        await db.commit()
        await db.close()


async def set_match_winner(match_id, winner):
    async with aiosqlite.connect('fantasyDB/fantasy.db') as db:
        set_match_winner_text = '''
                                UPDATE matches
                                SET radiant_win = %d
                                WHERE match_id = '%s' ''' % (winner, match_id)

        await db.execute(set_match_winner_text)
        await db.commit()
        await db.close()


async def set_match_unfinished(match_id):
    async with aiosqlite.connect('fantasyDB/fantasy.db') as db:
        set_match_unfinished_text = '''
                                    UPDATE matches
                                    SET unfinished = 1
                                    WHERE match_id = '%s' ''' % match_id

        await db.execute(set_match_unfinished_text)
        await db.commit()
        await db.close()


# message functions
async def add_message(bot_id, match_id, channel_id, message_id):
    async with aiosqlite.connect('fantasyDB/fantasy.db') as db:
        add_message_text = '''
                            INSERT INTO messages
                            (
                                bot_id,
                                match_id,
                                channel_id,
                                message_id
                            )
                            VALUES
                            (
                                '%s',
                                '%s',
                                '%s',
                                '%s'
                            )''' % (bot_id, match_id, channel_id, message_id)

        await db.execute(add_message_text)
        await db.commit()
        await db.close()


async def get_messages(bot_id, match_id):
    async with aiosqlite.connect('fantasyDB/fantasy.db') as db:
        get_messages_text = '''
                            SELECT
                                channel_id,
                                message_id
                            FROM
                                messages
                            WHERE bot_id = '%s' AND match_id = '%s' ''' % (bot_id, match_id)

        result = await db.execute(get_messages_text)
        messages = []
        async for row in result:
            messages.append([row[0], row[1]])

        await db.close()

        return messages


# bet functions
async def get_total_bets(match_id):
    async with aiosqlite.connect('fantasyDB/fantasy.db') as db:
        get_total_bets_text = '''
                                SELECT
                                    SUM(radiant_bet)    AS radiant_bet,
                                    SUM(dire_bet)       AS dire_bet
                                FROM
                                    bets
                                WHERE match_id = '%s' ''' % match_id

        result = await db.execute(get_total_bets_text)
        total_bets = await result.fetchone()
        await db.close()

        if total_bets:
            return [total_bets[0], total_bets[1]]
        else:
            return None


async def get_bets(match_id):
    async with aiosqlite.connect('fantasyDB/fantasy.db') as db:
        get_bets_text = '''
                        SELECT
                            user_id,
                            radiant_bet,
                            dire_bet
                        FROM
                            bets
                        WHERE match_id = '%s' ''' % match_id

        result = await db.execute(get_bets_text)

        bets = {}
        async for row in result:
            bets[row[0]] = [row[1], row[2]]

        await db.close()

        return bets


async def delete_bets(match_id):
    async with aiosqlite.connect('fantasyDB/fantasy.db') as db:
        delete_bets_text = '''
                            DELETE
                            FROM bets
                            WHERE match_id = '%s' ''' % match_id

        await db.execute(delete_bets_text)
        await db.commit()
        await db.close()


async def add_bets(match_id, user_id):
    async with aiosqlite.connect('fantasyDB/fantasy.db') as db:
        add_bets_text = '''
                        INSERT INTO bets
                        (
                            match_id,
                            user_id,
                            radiant_bet,
                            dire_bet
                        )
                        VALUES
                        (
                            '%s',
                            '%s',
                            0,
                            0
                        )''' % (match_id, user_id)

        await db.execute(add_bets_text)
        await db.commit()
        await db.close()


async def set_bets(match_id, user_id, radiant_bet, dire_bet):
    async with aiosqlite.connect('fantasyDB/fantasy.db') as db:
        set_bets_text = '''
                        UPDATE bets
                        SET
                            radiant_bet = %d,
                            dire_bet = %d
                        WHERE match_id = '%s' AND user_id = '%s' ''' % (radiant_bet, dire_bet, match_id, user_id)

        await db.execute(set_bets_text)
        await db.commit()
        await db.close()


# balance functions
async def get_balances():
    async with aiosqlite.connect('fantasyDB/fantasy.db') as db:
        get_balances_text = '''
                            SELECT
                                user_id,
                                balance
                            FROM
                                balances'''

        result = await db.execute(get_balances_text)

        balances = {}
        async for row in result:
            balances[row[0]] = row[1]

        await db.close()

        return balances


async def update_balance(user_id, balance):
    async with aiosqlite.connect('fantasyDB/fantasy.db') as db:
        update_balance_text = '''
                                UPDATE balances
                                SET balance = %d
                                WHERE user_id = '%s' ''' % (balance, user_id)

        await db.execute(update_balance_text)
        await db.commit()
        await db.close()


async def add_balance(user_id):
    async with aiosqlite.connect('fantasyDB/fantasy.db') as db:
        add_balance_text = '''
                            INSERT INTO balances
                            (
                                user_id,
                                balance
                            )
                            VALUES
                            (
                                '%s',
                                1000
                            )''' % user_id

        await db.execute(add_balance_text)
        await db.commit()
        await db.close()
