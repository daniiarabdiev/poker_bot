import pandas as pd
import sys


class Printer():
    """Print things to stdout on one line dynamically"""
    def __init__(self,data):
        sys.stdout.write("\r\x1b[K"+data.__str__())
        sys.stdout.flush()


raw_data = pd.read_csv('data/2020-06-15.csv')


raw_data = raw_data.loc[raw_data['type1'] == "Hold'em No Limit"].copy()

number_of_hands = len(set(raw_data['hand_id']))

raw_data.drop_duplicates(inplace=True)


all_hands_all_states = []
count = 0
for hand_id, hand in raw_data.groupby('hand_id'):
    
    hand.drop_duplicates(subset=['hand_id', 'num_of_step'], inplace=True)
    
    hand.sort_values(by='num_of_step', inplace=True)
    
    hand = hand.reset_index()
    
    my_seat_num = hand["my_seat_num"].iloc[0]
    my_id = hand[f'Seat_{my_seat_num}_id'].copy().iloc[0]
    
    my_action_indexes = hand.loc[hand.user_step_id == my_id].copy().index.tolist()
    
    my_result = hand[f'result_seat{my_seat_num}'].iloc[-1]

    hand_states = []
    for index in my_action_indexes:
        state = hand.iloc[:index+1].copy()
        hand_states.append(state)

    my_state = []
    for state_df in hand_states:
        
        my_action_type = state_df.action_type.iloc[-1]
        my_action_sum = state_df.action_sum.iloc[-1]
        step_num = state_df.num_of_step.iloc[-1]
        sum_action_sum = sum(state_df.action_sum)
        
        mycard11 = state_df['my_card_11'].iloc[0]
        mycard12 = state_df['my_card_12'].iloc[0]
        mycard21 = state_df['my_card_21'].iloc[0]
        mycard22 = state_df['my_card_22'].iloc[0]
        
        table_cards = state_df[['FLOP_11', 'FLOP_12', 'FLOP_21', 'FLOP_22', 'FLOP_31', 'FLOP_32', 'TURN_11', 'TURN_12', 'RIVER_11', 'RIVER_12']].copy()
        
        flop11 = table_cards.iloc[-1, 0]
        flop12 = table_cards.iloc[-1, 1]
        flop21 = table_cards.iloc[-1, 2]
        flop22 = table_cards.iloc[-1, 3]
        flop31 = table_cards.iloc[-1, 4]
        flop32 = table_cards.iloc[-1, 5]
        turn11 = table_cards.iloc[-1, 6]
        turn12 = table_cards.iloc[-1, 7]
        river11 = table_cards.iloc[-1, 8]
        river12 = table_cards.iloc[-1, 9]
        
        stage = state_df['stage'].iloc[-1]
        
        type_2 = state_df['type2'].iloc[0]
        type_3 = state_df['type3'].iloc[0]
        
        table_id = state_df['table_id'].iloc[0]
        button_id = state_df['button_id'].iloc[0]
        
        a = state_df[f'Seat_{hand["my_seat_num"].iloc[0]}_in_chips']
        
        try:
            money_i_have = a.iloc[-2]
        except:
            money_i_have = a.iloc[-1]
            
        bank_before = state_df['bank_before'].iloc[-1]
        
        actions_d2 = dict()
        for i in range(1, 11):
            for s in ['pre-flop', 'flop', 'turn', 'river']:
                for step in range(1, 3):
                    actions_d2[f'{s}_player_{i}_action_type_{step}'] = 'unknown'
                    actions_d2[f'{s}_player_{i}_action_sum_{step}'] = -1
                    actions_d2[f'{s}_player_{i}_money_had_{step}'] = -1
        
        seats = state_df[[f'Seat_{i}_id' for i in range(1, 11)]].copy().iloc[-1].to_dict()
        
        seats_inv = {v: k for k, v in seats.items()}
        
        for row in state_df.iloc[:-1].itertuples():
            seat_number = seats_inv[row.user_step_id].split('_')[1]
            
            if actions_d2[f'{row.stage}_player_{seat_number}_action_type_1'] == 'unknown':
                actions_d2[f'{row.stage}_player_{seat_number}_action_type_1'] = row.action_type
                actions_d2[f'{row.stage}_player_{seat_number}_action_sum_1'] = row.action_sum
                actions_d2[f'{row.stage}_player_{seat_number}_money_had_1'] = row[state_df.columns.get_loc(f'Seat_{seat_number}_in_chips') + 1]
            else:
                actions_d2[f'{row.stage}_player_{seat_number}_action_type_2'] = row.action_type
                actions_d2[f'{row.stage}_player_{seat_number}_action_sum_2'] = row.action_sum
                actions_d2[f'{row.stage}_player_{seat_number}_money_had_2'] = row[state_df.columns.get_loc(f'Seat_{seat_number}_in_chips') + 1]
        
        x_state = {
            'unique_id': f'{my_id}_{table_id}_{hand_id}_{step_num}',
            'step_num': step_num,
            'hand_id': hand_id,
            'my_id': my_id,
            'my_seat_num': my_seat_num,
            'mycard11': mycard11,
            'mycard12': mycard12,
            'mycard21': mycard21,
            'mycard22': mycard22,
            'flop11': flop11,
            'flop12': flop12,
            'flop21': flop21, 
            'flop22': flop22,
            'flop31': flop31, 
            'flop32': flop32,
            'turn11': turn11,
            'turn12': turn12, 
            'river11': river11, 
            'river12': river12,
            'stage': stage,
            'type2': type_2,
            'type3': type_3,
            'table_id': table_id,
            'button_id': button_id,
            'money_i_have': money_i_have,
            'bank_before': bank_before
        }
        
        x_state.update(actions_d2)
        
        x_state.update({'my_action_type': my_action_type, 
                       'my_action_sum': my_action_sum,
                       'sum_action_sum': sum_action_sum,
                       'my_result': my_result})
        
        my_state.append(x_state)
    
    my_hand_states_df = pd.DataFrame(my_state)
    all_hands_all_states.append(my_hand_states_df)
    count += 1
    if count % 100 == 0:
        Printer(f'{count} out of {number_of_hands}')

all_hands_all_states_df = pd.concat(all_hands_all_states)
all_hands_all_states_df.to_csv('data/all_hands_all_states_df.csv', index=False)