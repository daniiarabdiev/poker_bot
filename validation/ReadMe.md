# Poker bot evaluation

Poker bot evaluation using bot actions and top player actions to compare. Also includes, scripts to parse hh files to structured csv form, and processing scripts from structured hand repressentation to structured state representation.  

## How to replicate results

  - Run parser.py to convert HH files to structered hand representation SHR files(2020-06-15.csv)
  - Run convert_to_states.py to convert from SHR (2020-06-15.csv) file to action state representations (all_hands_all_states_df.csv)
  - Run get_top_player_states.py to get top players states (top_player_states.csv)
  - Run hh_to_bot.py to get bot actions from API and get (good_players_bot.csv)
  - Run validation.py to get validation metric comparing bot's actions to top players. 