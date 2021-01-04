import pandas as pd


def min_max(arr):
    minmax_arr = (arr - min(arr))/(max(arr) - min(arr))
    return minmax_arr


def trend_change(arr):
    trend_change = 0
    for i in range(len(arr)-1):
        trend_change += abs(arr[i] - arr[i+1])
    return trend_change


def calc_trend_changes_encode_seq(arr_seq):
    d = {'r': 1, 'k':1, 'c': 1, 'b': 1, 'f': 0}
    res_arr = []
    for i in arr_seq:
        res = list(map(lambda x: d[x], i))
        number_of_trend_changes = trend_change(res)
        res_arr.append(number_of_trend_changes)
    return res_arr


def create_codepage(letters):
    return {k: v for v, k in enumerate(letters)}


def hensel_encode(X, cp):
    """Hensel encoding (embedding, vectorizing) of the word induced by given codepage.

    Args:
        X (array of chars): array of letters
        cp (dict): dict of pairs {char: integer}

    Returns:
        list: vector of integers representing the word characters
    """
    p = len(cp)
    return [cp[Xi] * p ** i for i, Xi in enumerate(reversed(X))]


def abs_diff(x, y):
    '''
    Component-wise absolute difference of the given vectors components
    Args:
        x (array of ints): array of integers representing the left word letters
        y (array of ints): array of integers representing the right word letters

    Returns:
        list: list of integers representing the component-wise difference between given vectors
    '''
    return [abs(xi - yi) for xi, yi in zip(x, y)]


def owl_norm(w, x):
    '''
    Evaluates OWL-norm of the given vector induced by the weighted vector w

    Args:
        weights (list of floats): list of the norm weights
        x (list of ints): integer vector to be normed

    Returns:
        float: OWL-norm value of x induced by weights vector w
    '''
    return sum([wi * xi for wi, xi in zip(w, x)])


def owl_dist(w, x, y):
    '''
    Evaluates OWL distance between two vectors induced by the weighted vector w

    Args:
        weights (list of floats): list of the norm weights
        x (list of ints): first integer vector to be normed
        y (list of ints): second integer vector to be normed

    Returns:
        float: OWL-distance value of x induced by weights vector w
    '''
    return owl_norm(w, abs_diff(x, y))


def encoding_func(df, my_actions_col, other_actions_col):
    letters = ['f', 'k', 'c', 'b', 'r']
    weights = [0.5, 0.6, 0.7, 0.8, 0.9]
    cp = create_codepage(letters)

    y1 = []
    for seq in df[my_actions_col]:
        x = hensel_encode(list(seq), cp)
        y1.append(x)

    y2 = []
    for seq in df[other_actions_col]:
        x = hensel_encode(list(seq), cp)
        y2.append(x)

    dxys = []
    for pair in zip(y1, y2):
        dxy = owl_dist(weights, pair[0], pair[1])
        dxys.append(dxy)

    return dxys


def main():

    one_player_df = pd.read_csv('data/good_players_bot.csv')

    one_player_df_sample = one_player_df[['my_action_type', 'my_action_sum', 'sum_action_sum',
                                          'my_result', 'seq_encod', 'my_result_binary', 'bot_action_type',
                                          'bot_action_sum', 'encod']].copy()

    one_player_df_sample['bot_action_type'] = one_player_df_sample['bot_action_type'].apply(lambda x: 'raise' if x == 'allin' else x)

    one_player_df_sample['absprofit'] = abs(one_player_df_sample['my_result'])
    one_player_df_sample['min_max_absprofit'] = min_max(one_player_df_sample['my_result'])
    pw1 = one_player_df_sample.loc[one_player_df_sample['my_result_binary'] == 1]['min_max_absprofit']
    pw0 = one_player_df_sample.loc[one_player_df_sample['my_result_binary'] == 0]['min_max_absprofit']

    one_player_df_sample['random_trend_changes'] = calc_trend_changes_encode_seq(one_player_df_sample['encod'])
    one_player_df_sample['bot_trend_changes'] = calc_trend_changes_encode_seq(one_player_df_sample['seq_encod'])


    # trend manipulations
    one_player_df_sample['random_trend_changes'] = one_player_df_sample['random_trend_changes'].apply(lambda x: 1 if x==0 else x)
    one_player_df_sample['bot_trend_changes'] = one_player_df_sample['bot_trend_changes'].apply(lambda x: 1 if x==0 else x)


    w1_df = one_player_df_sample.loc[one_player_df_sample['my_result_binary'] == 1].copy()
    w0_df = one_player_df_sample.loc[one_player_df_sample['my_result_binary'] == 0].copy()

    w1_df['diff'] = abs(w1_df['bot_action_sum'] - w1_df['my_action_sum']) * pw1
    w0_df['diff'] = abs(w0_df['bot_action_sum'] - w0_df['my_action_sum']) * pw0

    w1_df['minmax_diff'] = min_max(w1_df['diff'])
    w0_df['minmax_diff'] = min_max(w0_df['diff'])


    random_diff1 = w1_df['minmax_diff'].mean() - w0_df['minmax_diff'].mean()

    one_player_df_sample['random_encod_diff'] = encoding_func(one_player_df_sample, 'seq_encod', 'encod')

    one_player_df_sample['random_min_max_encod_diff'] = min_max(one_player_df_sample['random_encod_diff'])

    w1_df['random_encod_diff'] = one_player_df_sample.loc[one_player_df_sample['my_result_binary'] == 1]['random_encod_diff']

    w0_df['random_encod_diff'] = one_player_df_sample.loc[one_player_df_sample['my_result_binary'] == 0]['random_encod_diff']

    w1_df['random_min_max_encod_diff'] = one_player_df_sample.loc[one_player_df_sample['my_result_binary'] == 1]['random_min_max_encod_diff']

    w0_df['random_min_max_encod_diff'] = one_player_df_sample.loc[one_player_df_sample['my_result_binary'] == 0]['random_min_max_encod_diff']


    random_enc_diff = w1_df['random_min_max_encod_diff'].mean() - w0_df['random_min_max_encod_diff'].mean()


    # All we care about is whether one bot is more inconsistent than the other bot.
    # If inconsistency is measured by trend changes, we can calculate average trend changes for Bot1 and Bot2

    one_player_df_sample['minmax_random_trend_changes'] = min_max(one_player_df_sample['random_trend_changes'])
    one_player_df_sample['minmax_bot_trend_changes'] = min_max(one_player_df_sample['bot_trend_changes'])

    total_number_of_inconsistent_games_random = sum([1 if i > 1 else 0 for i in one_player_df_sample['random_trend_changes']])

    ratio_of_inconsistent_random = total_number_of_inconsistent_games_random / len(one_player_df_sample['random_trend_changes'])

    total_number_of_inconsistent_games_bot = sum([1 if i>1 else 0 for i in one_player_df_sample['bot_trend_changes']])

    ratio_of_inconsistent_bot = total_number_of_inconsistent_games_bot / len(one_player_df_sample['bot_trend_changes'])

    # Combine Action Sum difference, Action Sequences Difference and inconsistency difference and possibly profit in one formula that has a range of [-inf;0;+inf] where -inf mean B1 better than B2, and 0 means B1 is the same as B2

    random_total_diff = (random_diff1 + random_enc_diff + (ratio_of_inconsistent_random - ratio_of_inconsistent_bot)) / 3

    return random_total_diff


if __name__=='__main__':
    metric = main()
    print(f'From [-1, 1] the difference between two bots is {metric}')

