import pandas as pd


def get_number_of_players_per_hand(raw_out):
    hands = []
    for hand_id, hand_df in raw_out.groupby('hand_id'):
        users = set(hand_df['user_step_id'])
        hands.append([hand_id, len(users)])

    hand_len_df = pd.DataFrame(hands, columns=['hand_id', 'number_of_players'])

    return hand_len_df


def get_results(all_states):
    results = []
    for play in all_states.groupby(['hand_id', 'my_id']):
        results.append([play[1].my_id.iloc[0], play[1].my_result.iloc[0]])
    results_df = pd.DataFrame(results)
    results_df.columns = ['user_id', 'user_result']
    return results_df


def main():

    raw_out = pd.read_csv('data/2020-06-15.csv')
    all_states = pd.read_csv('data/all_hands_all_states_df.csv')

    hand_len_df = get_number_of_players_per_hand(raw_out)

    six_hands = hand_len_df.loc[hand_len_df['number_of_players']>5].copy()  # get only 6 player hands

    all_states = all_states[all_states['hand_id'].isin(six_hands['hand_id'].tolist())].copy()

    results_df = get_results(all_states)

    result_s_df = results_df.groupby('user_id').agg({'user_result': ['sum', 'count']}).reset_index()

    result_s_df.columns = ['_'.join(col) for col in result_s_df.columns.values]

    result_s_df['average_per_game'] = result_s_df['user_result_sum'] / result_s_df['user_result_count']

    result_s_df.dropna(inplace=True)

    result_s_df = result_s_df.sort_values(by=['average_per_game'], ascending=False)

    print(result_s_df.head(5))

    a = all_states[all_states['my_id'].isin(result_s_df.head(5)['user_id_'].tolist())].copy()

    a.to_csv('data/top_player_states.csv', index=False)