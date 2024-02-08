import init_deck
import random 
from royal_hold_em_cfr_parallel import determine_player, get_legal_actions, is_terminal, is_flop_chance, terminal_util, intersection
import time 




def construct_float(num_string):
    num = num_string.strip(" ")
    num = num.strip("'")
    return float(num)


def get_possible_flops(agent_map,player_1_cards_translated):
    possible_flops = [] 

    for i_set in agent_map:
        n_cards = 0 
        for part in i_set.split(" "):
            if part in init_deck.card_dictionary:
                n_cards += 1 
        if n_cards > 2: # there is a flop in this string 
            flop_cards = [part for part in i_set.split(" ") if part in init_deck.card_dictionary]
            flop_cards = flop_cards[2:]
            if len(intersection(flop_cards,player_1_cards_translated)) == 0: #player 1 cards are not part of this flop, we can use it 
                possible_flops.append(flop_cards)

    return possible_flops            

def get_agent_map(agent_cards):
    card_pair_string = agent_cards[0] + " " + agent_cards[1]
    i_map = open("cfr_strategy_table.txt", "r")
    information_sets = i_map.readlines() 
    reverse_flag = False
    agent_map = []
    for i_set in information_sets: 
        if i_set.startswith(card_pair_string): 
            i_set = i_set.strip() # strip line terminator \n 
            agent_map.append(i_set) 


    if len(agent_map) == 0:
        reverse_flag = True 
        card_pair_string = agent_cards[1] + " " + agent_cards[0]
        i_map = open("cfr_strategy_table.txt", "r")
        information_sets = i_map.readlines() 
        agent_map = []
        for i_set in information_sets: 
            if i_set.startswith(card_pair_string):
                i_set = i_set.strip() # strip line terminator \n 
                agent_map.append(i_set) 

    return_tuple = [agent_map,reverse_flag]    
         
    return return_tuple


def find_information_set(agent_history, agent_map): 
    i_set_line = ""
    for i_set in agent_map:
        i_set_key = i_set.split(" [")[0] # get the key from the information set  
        if i_set_key == agent_history:
            i_set_line = i_set # information set line found 
    
    if i_set_line == "": 
        print("Information set not found!")
        return main()
    probability_vector_strings = i_set_line.split(" [")[1].split("]")[0].split(",") # ah yes 
    probability_vector = [construct_float(x) for x in probability_vector_strings] 

    return probability_vector


def main():
    print("Welcome to Royal Flop Poker! Please enter buy in amount: ")
    balance = int(input())
    init_game(balance,balance)


def init_game(player_1_balance, player_2_balance): 
    print("* ------------------------------------------------------------------- * ")
    print("Game begins! Bet amounts are: 10, 50, 100")
    print("Deal cards? Y/N")
    user_input = input()
    if(user_input in "Yy"):
        print("* ------------------------------------------------------------------- * ")
        deck = init_deck.deck
        random.shuffle(deck)
    
        player_1_cards = []
        player_2_cards = []

        history = "" # This history is used for managing the game state, and to determine legal actions etc. 

        agent_history = "" # This history is used in the lookup of the Blueprint Strategy 

        # Do a poker style deal of the cards, making sure to remove them from the deck as well by using pop
        player_1_cards.append(deck[0])
        player_2_cards.append(deck[1])
        player_1_cards.append(deck[2])
        player_2_cards.append(deck[3])
        
        player_1_cards_translated = [init_deck.card_to_string(player_1_cards[0]),init_deck.card_to_string(player_1_cards[1])] # Translate cards from their integer representations to a readable string 
        player_2_cards_translated = [init_deck.card_to_string(player_2_cards[0]),init_deck.card_to_string(player_2_cards[1])]


        player_2_cards_translated.sort() 
        player_1_cards_translated.sort()
        print("Your cards are: " + player_1_cards_translated[0] + " " + player_1_cards_translated[1]) 

        print("You bet 10 chips as the small blind!") # Player 1 has to bet the small blind 
    

        history += "r r b10" 
        
       
        #print(history)
        #print(agent_history) 

        agent_map_tuple = get_agent_map(player_2_cards_translated)

        rev_flag = agent_map_tuple[1]
        agent_map = agent_map_tuple[0]

        if rev_flag:
             agent_history += player_2_cards_translated[1] + " "  + player_2_cards_translated[0] + " " + history 
        else:
             agent_history += player_2_cards_translated[0] + " "  + player_2_cards_translated[1] + " " + history      
        
        while(True):
            n = determine_player(history)
            if is_terminal(history):
                
                player_participation = terminal_util(history,player_1_cards[0],player_1_cards[1],player_2_cards[0],player_2_cards[1])
                
                if (player_participation > 0):
                    print("Congratulations! You've won: " + str(player_participation))
                    print("Opponent had: " + str(player_2_cards_translated[0]) + " "+str(player_2_cards_translated[1]))
                    print("Your new balance is: " + str(player_1_balance + player_participation))
                    print("Opponents balance: " + str(player_2_balance-player_participation))
                    return init_game(player_1_balance+player_participation, player_2_balance-player_participation)
                

                elif (player_participation < 0):
                    player_participation = (-1) * player_participation 
                    print("You lost: " + str(player_participation))
                    print("Opponent had: " + str(player_2_cards_translated[0]) + " " + str(player_2_cards_translated[1]))
                    print("Your new balance is: " + str(player_1_balance-player_participation))
                    print("Opponents balance: " + str(player_2_balance+player_participation))
                    return init_game(player_1_balance-player_participation, player_2_balance+player_participation)

                else: 
                    print("Opponent either folded pre-flop or the pot was split evenly") 
                    print("Opponent had: " + str(player_2_cards_translated[0]) + " " + str(player_2_cards_translated[1])) 
                    return init_game(player_1_balance, player_2_balance)  
                
            if is_flop_chance(history):
                flops = get_possible_flops(agent_map,player_1_cards)
                flop = random.choice(flops)
                flop_string = str(flop[0]) + " " + str(flop[1]) + " " + str(flop[2])  
                print("Flop comes: " + flop_string)
                history += " r " + flop_string 
                agent_history += " r " + flop_string 
                continue 
           
            if (n%2 == 0): #its our turn to make a choice 
                print("It's your turn! Make a choice!") 
                legal_actions = get_legal_actions(history)
                print("Choose one of the following actions! ") 
                print(legal_actions)
                user_choice = legal_actions[int(input())] 
                history += " " + user_choice
                agent_history += " "  + user_choice 
            else: # agent makes a choice 
                print("Opponent is making a choice!")
                time.sleep(3)
                decision_probability_vector = find_information_set(agent_history,agent_map)
                legal_actions = get_legal_actions(history)
                agent_choice = random.choices(legal_actions,decision_probability_vector)[0]
                history += " " + agent_choice
                agent_history += " " + agent_choice
                print("Opponent chooses: " + agent_choice)
                #print(legal_actions)
                





    elif(user_input in "Nn"):
        main()

    else:
        print("Please input Y or N")
        init_game(player_1_balance,player_2_balance)





if __name__ == "__main__":
   main()


