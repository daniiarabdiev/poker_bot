import os
import re
import pandas as pd
from time import time
import sys


start = time()


class Printer():
    """Print things to stdout on one line dynamically"""
    def __init__(self,data):
        sys.stdout.write("\r\x1b[K"+data.__str__())
        sys.stdout.flush()


for folder in os.listdir('relevant_data/hh/files')[2:]: # change that

    all_united_hands = []

    count = 1

    all_files = os.listdir(f'relevant_data/hh/files/{folder}')

    for filename in all_files:

        with open(os.path.join(f'relevant_data/hh/files/{folder}', filename), 'r') as rfile:
            hands = rfile.read().split('\n\n')

        Printer(f'Filename is {filename}, {count} out of {len(all_files)}')

        for hand in hands:
            try:

                hand = hand.strip()
                lines = hand.split('\n')

                if len(lines) <= 2:
                    continue

                if 'Dealt' not in hand:
                    continue

                first_line = lines[0]
                second_line = lines[1]

                hand_prefix = first_line.strip().split(' ')[0]
                hand_id = first_line.strip().split(' ')[2]

                type1 = ' '.join(first_line.split('(')[0].strip().split(' ')[-3:])

                type2 = first_line[first_line.find("(") + 1:first_line.find(")")]

                type22 = type2.split('/')[0].strip()[1:]
                type3 = type2.split('/')[1].strip()[1:].strip().split(' ')[0]
                currency = type2.split('/')[1].strip()[1:].strip().split(' ')[1]

                table_id = second_line.split("'")[1]

                max_table = second_line.split("'")[2].strip().split(' ')[0]
                button_id = second_line.split("'")[2].strip().split(' ')[2]

                seats = {}
                blinds = {}
                number_of_blinds = 0
                my = {}
                board_cards = []
                col_cards = ['FLOP_11', 'FLOP_12', 'FLOP_21', 'FLOP_22', 'FLOP_31', 'FLOP_32', 'TURN_11', 'TURN_12', 'RIVER_11',
                             'RIVER_12']

                format_seats = {f'Seat_{seat_number}_id': '' for seat_number in range(1, 11)}
                format_seats.update({f'Seat_{seat_number}_in_chips': '' for seat_number in range(1, 11)})

                all_seats = []
                hand_actions = []

                num_of_step = 0
                stage = 'pre-flop'
                errors = 0
                winners = {}
                for line in lines[2:]:
                    if 'Seat' in line:
                        user_id = line.split(':')[1].split('(')[0].strip()
                        seats[user_id] = {'seat_num': line.split(' ')[1].replace(':', ''),
                                                     'user_chips': re.sub("[^0-9.]", "", line.split('(')[1]),
                                                     'result_seat': 0}
                        format_seats[f"Seat_{line.split(' ')[1].replace(':', '')}_id"] = user_id
                        format_seats[f"Seat_{line.split(' ')[1].replace(':', '')}_in_chips"] = seats[user_id]['user_chips']
                        continue

                    elif 'blind' in line:
                        if 'small' in line:
                            small_blind_id = line.split(':')[0].strip()
                            small_blind_sum = re.sub("[^0-9.]", "", line.split(':')[1])
                            blinds['small_blind_id'] = small_blind_id
                            blinds['small_blind_sum'] = small_blind_sum
                            seats[small_blind_id]['result_seat'] -= float(small_blind_sum)
                        else:
                            big_blind_id = line.split(':')[0].strip()
                            big_blind_sum = re.sub("[^0-9.]", "", line.split(':')[1])
                            blinds['big_blind_id'] = big_blind_id
                            blinds['big_blind_sum'] = big_blind_sum
                            seats[big_blind_id]['result_seat'] -= float(big_blind_sum)

                        number_of_blinds += 1
                        continue

                    elif 'Dealt' in line:
                        my_user_id = line.strip().split(' ')[2]
                        my_cards = line.split('[')[1].replace(']', '')
                        my['my_card_11'] = my_cards.split(' ')[0][0]
                        my['my_card_12'] = my_cards.split(' ')[0][1]
                        my['my_card_21'] = my_cards.split(' ')[1][0]
                        my['my_card_22'] = my_cards.split(' ')[1][1]
                        my['my_seat_num'] = seats[my_user_id]['seat_num']

                        try:
                            bank_before = float(blinds['small_blind_sum']) + float(blinds['big_blind_sum'])
                        except KeyError:
                            errors += 1
                            break

                        continue

                    elif '***' in line:
                        if 'FLOP' in line:
                            stage = 'flop'
                            board_cards = []
                            b_cards = line.split('***')[-1].strip().replace('[', '').replace(']', '').split(' ')
                            for card in b_cards:
                                board_cards.append(card[0])
                                board_cards.append(card[1])
                        elif 'TURN' in line:
                            stage = 'turn'
                            board_cards = []
                            b_cards = line.split('***')[-1].strip().replace('[', '').replace(']', '').split(' ')
                            for card in b_cards:
                                board_cards.append(card[0])
                                board_cards.append(card[1])
                        elif 'RIVER' in line:
                            stage = 'river'
                            board_cards = []
                            b_cards = line.split('***')[-1].strip().replace('[', '').replace(']', '').split(' ')
                            for card in b_cards:
                                board_cards.append(card[0])
                                board_cards.append(card[1])
                        continue

                    elif ':' in line:
                        num_of_step += 1
                        user_step_id = line.split(':')[0].strip()
                        action_type = line.split(' ')[1].strip()
                        if 'folds' in line.strip():
                            action_sum = 0.0
                            show_cards = ''
                        elif 'checks' in line.strip():
                            action_sum = 0.0
                            show_cards = ''
                        elif 'shows' in line.strip():
                            action_sum = 0.0
                            show_cards = line.strip().split('[')[-1].replace(']', '')
                        else:
                            action_sum = re.sub("[^0-9.]", "", line.strip().split(' ')[-1])
                            show_cards = ''

                        if show_cards != '':
                            show_card11 = show_cards.strip().split(' ')[0][0]
                            show_card12 = show_cards.strip().split(' ')[0][1]
                            show_card21 = show_cards.strip().split(' ')[1][0]
                            show_card22 = show_cards.strip().split(' ')[1][1]
                        else:
                            show_card11 = ''
                            show_card12 = ''
                            show_card21 = ''
                            show_card22 = ''

                        bank_after = float(bank_before) + float(action_sum)

                        board_cards = board_cards + ['' for i in range(len(col_cards) - len(board_cards))]
                        format_seats[f"Seat_{seats[user_step_id]['seat_num']}_in_chips"] = float(format_seats[f"Seat_{seats[user_step_id]['seat_num']}_in_chips"]) - float(action_sum)

                        all_seats.append([format_seats[k] for k in format_seats])

                        seats[user_step_id]['result_seat'] = float(seats[user_step_id]['result_seat']) - float(action_sum)

                        #print(stage, num_of_step, user_step_id, action_type, action_sum, show_cards, bank_before, bank_after, board_cards)

                        row = board_cards + [num_of_step, stage, user_step_id, action_type, bank_before, action_sum, bank_after,
                                             show_card11, show_card12, show_card21, show_card22]
                        hand_actions.append(row)

                        bank_before = float(bank_after)

                    elif 'collected' in line:
                        winner_id = line.split('collected')[0].strip()
                        winner_sum = re.sub("[^0-9.]", "", line.split('collected')[1])
                        seats[winner_id]['result_seat'] += float(winner_sum)
                    elif 'Uncalled' in line:
                        winner_id = line.split('returned to')[-1].strip()
                        winner_sum = re.sub("[^0-9.]", "", line.split(' ')[2])
                        seats[winner_id]['result_seat'] += float(winner_sum)

                if number_of_blinds > 2:
                    continue

                if errors > 0:
                    continue

                all_seats_cols = [f'Seat_{i}_id' for i in range(1, 11)] + [f'Seat_{i}_in_chips' for i in range(1, 11)]
                all_seats_df = pd.DataFrame(all_seats, columns=all_seats_cols)

                # putting everything together
                hand_info = {'hand_prefix': hand_prefix, 'hand_id': hand_id, 'type1': type1, 'type2': type22, 'type3': type3,
                             'currency': currency, 'table_id': table_id, 'max_table': max_table, 'button_id': button_id}

                static_info = {}

                static_info.update(hand_info)
                static_info.update(my)
                static_info.update(blinds)

                hand_actions_df = pd.DataFrame(hand_actions, columns=col_cards + ['num_of_step', 'stage', 'user_step_id',
                                                                                  'action_type', 'bank_before', 'action_sum',
                                                                                  'bank_after', 'show_card_11', 'show_card_12',
                                                                                  'show_card_21', 'show_card_22'])

                static_info_df = pd.DataFrame({k:[static_info[k]] for k in static_info})

                static_info_df = pd.concat([static_info_df for _ in range(hand_actions_df.shape[0])]).reset_index().drop(['index'], axis=1)

                res_d = {}
                seat_nums = []
                for k in seats:
                    res_d[f"result_seat{seats[k]['seat_num']}"] = [seats[k]['result_seat']]
                    seat_nums.append(int(seats[k]['seat_num']))

                for i in range(max(seat_nums), 11):
                    res_d[f"result_seat{i}"] = ['']

                res_df = pd.DataFrame(res_d)

                emp_df = pd.DataFrame([['' for _ in range(10)] for _ in range(hand_actions_df.shape[0] - 1)], columns=list(res_d))

                res_df = pd.concat([emp_df, res_df]).reset_index().drop('index', axis=1)

                united_df = pd.concat([static_info_df, all_seats_df, hand_actions_df, res_df], axis=1)

                all_united_hands.append(united_df)
            except:
                lines = hand.split('\n')
                print('\n\n', filename, lines[0], lines[1], '\n')

        count += 1

    all_united_hands_df = pd.concat(all_united_hands)

    all_united_hands_df.to_csv(f'data/{folder}.csv', index=False)

    print(time() - start)