import pandas as pd


raw_data = pd.read_csv('data/2020-06-15.csv')

raw_data.drop_duplicates(inplace=True)


raw_data = raw_data.loc[raw_data['type1'] == "Hold'em No Limit"].copy()


all_hands_all_states = []
count = 0
for hand_id, hand in raw_data.groupby('hand_id'):
    
    hand.drop_duplicates(subset=['hand_id', 'num_of_step'], inplace=True)
    
    hand.sort_values(by='num_of_step', inplace=True)
    hand = hand.reset_index()
    
    seats_numbers = hand[[f'Seat_{i}_id' for i in range(1, 11)]].iloc[0].to_dict()
    
    seats_numbers = {v: k for k, v in seats_numbers.items()}
    
    for username in set(hand['user_step_id']):
        
        user_action_indexes = hand.loc[hand.user_step_id == username].copy().index.tolist()
        seat_num = seats_numbers[username].split('_')[1]
        user_result = hand[f'result_seat{seat_num}'].iloc[-1]
        
        hand_states = []
        for index in user_action_indexes:
            state = hand.iloc[:index+1].copy()
            hand_states.append(state)
        
        user_states = []
        for state_df in hand_states:
            user_action_type = state_df.action_type.iloc[-1]
            user_action_sum = state_df.action_sum.iloc[-1]
            user_step_num = state_df.num_of_step.iloc[-1]
            
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
            
            a = state_df[f'Seat_{seat_num}_in_chips']
        
            try:
                money_user_has = a.iloc[-2]
            except:
                money_user_has = a.iloc[-1]

            bank_before = state_df['bank_before'].iloc[-1]

            actions_d2 = dict()
            for i in range(1, 11):
                for s in ['pre-flop', 'flop', 'turn', 'river']:
                    for step in range(1, 3):
                        actions_d2[f'{s}_player_{i}_action_type_{step}'] = 'unknown'
                        actions_d2[f'{s}_player_{i}_action_sum_{step}'] = -1
                        actions_d2[f'{s}_player_{i}_money_had_{step}'] = -1

            for row in state_df.iloc[:-1].itertuples():
                seat_number = seats_numbers[row.user_step_id].split('_')[1]

                if actions_d2[f'{row.stage}_player_{seat_number}_action_type_1'] == 'unknown':
                    actions_d2[f'{row.stage}_player_{seat_number}_action_type_1'] = row.action_type
                    actions_d2[f'{row.stage}_player_{seat_number}_action_sum_1'] = row.action_sum
                    actions_d2[f'{row.stage}_player_{seat_number}_money_had_1'] = row[state_df.columns.get_loc(f'Seat_{seat_number}_in_chips') + 1]
                else:
                    actions_d2[f'{row.stage}_player_{seat_number}_action_type_2'] = row.action_type
                    actions_d2[f'{row.stage}_player_{seat_number}_action_sum_2'] = row.action_sum
                    actions_d2[f'{row.stage}_player_{seat_number}_money_had_2'] = row[state_df.columns.get_loc(f'Seat_{seat_number}_in_chips') + 1]
            
            x_state = {
            'unique_id': f'{username}_{table_id}_{hand_id}_{user_step_num}',
            'user_step_num': user_step_num,
            'hand_id': hand_id,
            'user_id': username,
            'user_seat_num': seat_num,
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
            'money_i_have': money_user_has,
            'bank_before': bank_before
            }
        
            x_state.update(actions_d2)
        
            x_state.update({'user_action_type': user_action_type, 
                       'user_action_sum': user_action_sum,
                       'user_result': user_result})
        
            user_states.append(x_state)

        user_hand_states_df = pd.DataFrame(user_states)
        all_hands_all_states.append(user_hand_states_df)
    count += 1
    if count % 100 == 0:
        print(count)

all_hands_all_states_df = pd.concat(all_hands_all_states)
all_hands_all_states_df.to_csv('data/users_hands_all_states_df.csv', index=False)



