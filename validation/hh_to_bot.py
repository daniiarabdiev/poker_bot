import pandas as pd
import numpy as np
import requests


def multiply_float_to_int(df):
    for col in df.columns:
        if df[col].dtype == float:
            df[col] = df[col].apply(lambda x: x*1000)
    return df


def get_community_cards(row):

    cards = [row.flop11, row.flop12, row.flop21, row.flop22, row.flop31, row.flop32, row.turn11,
             row.turn12, row.river11, row.river12]

    community_cards = ''
    for card in cards:
        if card is not np.nan and card is not None:
            community_cards += card.upper()

    community_cards = [k + z for k, z in zip(community_cards[1:][::2], community_cards[::2])]
    return community_cards


def get_seats_in_chips(hand_df, seats, user_id, street):
    seats_in_chips = hand_df[[f'Seat_{i}_in_chips' for i in range(1, 11)]].copy().iloc[-1].to_dict()

    a = set(hand_df[hand_df['stage'] == street]['user_step_id'])

    json_seats = []
    for s in seats_in_chips:
        try:
            stack = int(seats_in_chips[s])
        except Exception as e:
            stack = 0
        p = s.split('_')[1]
        name = 'p' + str(p)

        uuid = seats[f'Seat_{p}_id']
        if uuid == user_id:
            name = 'ME'
        if uuid in a:
            player_state = 'participating'
        else:
            player_state = 'not participating'

        if type(uuid) == str:
            json_seats.append({'stack': stack, 'state': player_state, 'name': name, 'uuid': uuid})

    return json_seats


def get_action_history(hand_df, user_step_num, big_blind_amount, big_blind_id, small_blind_amount, small_blind_id):
    action_histories = {}

    for stage, stage_df in hand_df.groupby('stage'):
        all_stage_actions = []
        for rs in stage_df.itertuples():
            num_of_step = rs.num_of_step
            if user_step_num > num_of_step:
                action_user = rs.user_step_id
                action_action_type = rs.action_type
                action_action_sum = rs.action_sum

                all_stage_actions.append(
                    {'action': action_action_type[:-1], 'amount': int(action_action_sum), 'uuid': action_user})

        action_histories[stage] = all_stage_actions

    action_histories['preflop'].insert(0, {"action": "BIGBLIND", "amount": int(big_blind_amount), "uuid": big_blind_id})
    action_histories['preflop'].insert(0, {"action": "SMALLBLIND", "amount": int(small_blind_amount),
                                           "uuid": small_blind_id})

    return action_histories


def get_valid_actions(row, user_id, hand_df, street, user_step_num):
    valid_actions = []

    this_stage_df = hand_df[(hand_df['stage'] == street) & (hand_df['num_of_step'] < user_step_num)][
        ['user_step_id', 'action_type', 'action_sum']]

    valid_actions.append({'action': 'fold', 'amount': 0})

    if this_stage_df[this_stage_df['action_type'] == 'raises'].empty is False:
        latest_raise = this_stage_df[this_stage_df['action_type'] == 'raises'].iloc[-1]['action_sum']
        if latest_raise is not None:
            valid_actions.append({'action': 'call', 'amount': int(latest_raise)})
    else:
        latest_raise = 0
        valid_actions.append({'action': 'call', 'amount': 0})

    who_moved = this_stage_df['user_step_id'].value_counts().to_dict()

    if user_id in who_moved:
        if who_moved[user_id] > 2:
            pass
        else:
            valid_actions.append(
                {'action': 'raise', 'amount': {'max': int(row.money_i_have), 'min': int(latest_raise + 1)}})
    else:
        valid_actions.append(
            {'action': 'raise', 'amount': {'max': int(row.money_i_have), 'min': int(latest_raise + 1)}})

    return valid_actions


def send_request(common_dict):
    try:
        resp = requests.post('http://135.181.63.153:5001/get_action', json=common_dict)

        if resp.status_code == 200:
            bot_action_type = resp.json()[0]
            bot_action_sum = resp.json()[1]
            if bot_action_sum is None:
                bot_action_sum = 0
        else:
            print(common_dict)
            print('Error', resp)
            bot_action_type = 'Error'
            bot_action_sum = 'Error'
    except:
        bot_action_type = 'Errorwithrequest'
        bot_action_sum = 'Errorwithrequest'

    return bot_action_type, bot_action_sum


def get_bot_actions(raw_out, good_player_df):

    bot_actions = []
    for row in good_player_df.itertuples():

        unique_id = row.unique_id
        user_id = row.my_id
        user_step_num = row.step_num
        seat_num = row.my_seat_num

        one_card = (row.mycard12 + row.mycard11).upper()
        second_card = (row.mycard22 + row.mycard21).upper()

        hole_cards = [one_card, second_card]

        hand_id = row.hand_id

        hand_df = raw_out[(raw_out['hand_id'] == hand_id) & (raw_out['my_seat_num'] == seat_num)].copy()
        hand_df.sort_values(by=['num_of_step'], inplace=True)

        small_blind_id = hand_df['small_blind_id'].iloc[-1]
        big_blind_id = hand_df['big_blind_id'].iloc[-1]

        dealer_button = row.button_id.replace('#', '')

        seats = hand_df[[f'Seat_{i}_id' for i in range(1, 11)]].copy().iloc[-1].to_dict()

        seats_inv = {v: k for k, v in seats.items()}

        big_blind_pos = seats_inv[hand_df['big_blind_id'].iloc[-1]].split('_')[1]
        small_blind_pos = seats_inv[hand_df['small_blind_id'].iloc[-1]].split('_')[1]

        small_blind_amount = row.type2
        big_blind_amount = row.type3

        street = row.stage

        community_cards = get_community_cards(row)

        json_seats = get_seats_in_chips(hand_df, seats, user_id, street)

        pot = row.bank_before

        action_histories = get_action_history(hand_df, user_step_num, big_blind_amount,
                                              big_blind_id, small_blind_amount, small_blind_id)

        valid_actions = get_valid_actions(row, user_id, hand_df, street, user_step_num)

        round_count = 0
        next_player = 0

        common_dict = {
            'user_id': 0,
            'new_round': True,
            'round_state': {
                'round_count': round_count,
                'dealer_btn': int(dealer_button),
                'small_blind_pos': int(small_blind_pos),
                'big_blind_pos': int(big_blind_pos),
                'next_player': int(next_player),
                'small_blind_amount': int(small_blind_amount),
                'street': street,
                'community_card': community_cards,
                'seats': json_seats,
                'pot': {'main': {"amount": int(pot)}},
                'action_histories': action_histories
            },
            'valid_actions': valid_actions,
            'hole_card': hole_cards
        }

        #bot_action_type, bot_action_sum = send_request(common_dict)
        bot_action_type, bot_action_sum = 'Error', 'Error'
        bot_actions.append([unique_id, bot_action_type, bot_action_sum])

        print(row[0])

    bot_actions_df = pd.DataFrame(bot_actions, columns=['unique_id', 'bot_action_type', 'bot_action_sum'])

    return bot_actions_df


def main():
    raw_out = pd.read_csv('data/2020-06-15.csv')
    good_player_df = pd.read_csv('data/top_player_states.csv')

    raw_out = multiply_float_to_int(raw_out)

    raw_out['action_type'] = raw_out['action_type'].apply(lambda x: 'raises' if x=='bets' else x)

    raw_out['stage'] = raw_out['stage'].apply(lambda x: 'preflop' if x == 'pre-flop' else x)

    raw_out = raw_out[raw_out['action_type'].isin(['raises', 'checks', 'folds', 'calls'])].copy()

    good_player_df = good_player_df[good_player_df['my_action_type'].isin(['raises', 'checks', 'folds', 'calls'])].copy()

    good_player_df = multiply_float_to_int(good_player_df)

    good_player_df['my_action_type'] = good_player_df['my_action_type'].apply(lambda x: 'raises' if x == 'bets' else x)

    good_player_df['stage'] = good_player_df['stage'].apply(lambda x: 'preflop' if x == 'pre-flop' else x)

    bot_actions_df = get_bot_actions(raw_out, good_player_df)

    merged_df = good_player_df.merge(bot_actions_df, left_on='unique_id', right_on='unique_id', how='inner')

    merged_df.to_csv('data/good_players_bot.csv', index=False)

main()
