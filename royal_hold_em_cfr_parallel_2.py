import numpy as np
import arrays 
import init_deck 
import random 
import time
from concurrent.futures import ProcessPoolExecutor
from itertools import combinations
import multiprocessing
# r r b10 call10 r Ac Td Jd c b10 b20 b20 b20
deck = init_deck.deck 
DECK_LEN = len(deck)


def intersection(lst1, lst2):
    return list(set(lst1) & set(lst2))



def get_participation_difference(history):
    hist_parts = history.split(" ")
    bet_parts = [bet for bet in hist_parts if bet not in init_deck.card_dictionary and bet != 'r' and bet != 'c' and bet!='f']
    bets = [int(bet.split('call')[-1]) if 'call' in bet else int(bet.split('b')[-1]) for bet in bet_parts]
    
    p1_participation = sum(bets[::2])
    p2_participation = sum(bets[1::2])

    return abs(p1_participation - p2_participation)
    

def get_pot_amount(history):

    hist_parts = history.split(" ")
    bet_parts = [bet for bet in hist_parts if bet not in init_deck.card_dictionary and bet != 'r' and bet != 'c']
    bets = [int(bet.split('call')[-1]) if 'call' in bet else int(bet.split('b')[-1]) for bet in bet_parts]
    
    p1_participation = sum(bets[::2])
    p2_participation = sum(bets[1::2])

    return p1_participation + p2_participation


    

def list_rindex(li, x):
    for i in reversed(range(len(li))):
        if li[i] == x:
            return i

def find_fast(u):
    a, b, r = 0, 0, 0

    u = (u + 0xe91aaa35) & 0xFFFFFFFF
    u ^= u >> 16
    u = (u + (u << 8)) & 0xFFFFFFFF
    u ^= u >> 4
    b = (u >> 8) & 0x1ff
    a = ((u + (u << 2)) & 0xFFFFFFFF).to_bytes(4, 'little')
    a = int.from_bytes(a, 'little') >> 19
    r = a ^ arrays.hash_adjust[b]
    return r



def eval_5cards(c1, c2, c3, c4, c5):
    q = (c1 | c2 | c3 | c4 | c5) >> 16
    s = 0
    
    # This checks for Flushes and Straight Flushes
    if c1 & c2 & c3 & c4 & c5 & 0xf000:
        return arrays.flushes[q]

    # This checks for Straights and High Card hands
    if (s := arrays.unique5[q]):
        return s

    # This performs a perfect-hash lookup for remaining hands
    q = (c1 & 0xff) * (c2 & 0xff) * (c3 & 0xff) * (c4 & 0xff) * (c5 & 0xff)


    return arrays.hash_values[find_fast(q)]

    
#Actions : b10 b20 b50 call'amt' c f
 
def get_legal_actions(history):
    #print(history)
    if history == "r r": 
        return ["b10"]  # small blind 

    hist_parts = history.split(" ")
    
    participation_difference = get_participation_difference(history)
    call_action = 'call' + str(participation_difference)


    if participation_difference == 0: #check action possible
         return ['c', 'b10', 'b50', 'b100']
     
    legal_actions = []

    #print(participation_difference)
    legal_actions.append(call_action)

    if (len(hist_parts) < 4):
        possible_raises = [10,50,100] 
        possible_raises = ["b" + str(bet) for bet in possible_raises if bet > participation_difference]
        legal_actions.extend(possible_raises)

    legal_actions.append('f')

    
    return legal_actions






i_map = {}

def main():
    """
    Run iterations of counterfactual regret minimization algorithm.
    """
    global i_map # map of information sets
    n_iterations = 10
    expected_game_value = 0

    i = 1
    start = time.time()
    print ("CFR STARTS WITH " + str(n_iterations) +" ITERATIONS")
    for _ in range(n_iterations):
        iter_start = time.time()
        return_tuple = cfr(i_map)
        i_map = return_tuple[1]
        expected_game_value+=return_tuple[0]
        iter_end = time.time()
        print ("ITERATION COMPLETE " + str(i) + "/" + str(n_iterations) + " IN " + str(iter_end-iter_start) + " SECONDS ")
        i = i+1
        # for _, v in i_map.items(): # check speedup if each process seperately updates local imap 
        #     v.next_strategy()
        

    expected_game_value /= n_iterations
    end = time.time()
    print (str(n_iterations) + " ITERATIONS COMPLETE IN " +  str(end - start))
    display_results(expected_game_value, i_map)


def cfr(i_map, history="", p1_card1=-1,p1_card2 =-1, p2_card1=-1,  p2_card2=-1, pr_1=1, pr_2=1, pr_c=1):
    """
    Counterfactual regret minimization algorithm.

    Parameters
    ----------

    i_map: dict
        Dictionary of all information sets.
    history : r r b10 call10 ... string 
        A string representation of the game tree path we have taken.
        Each character of the string represents a single action:
        'r': random chance action
        'c': check action
        'b': bet action
    card_1 : (0, 2), int
        player A's card
    card_2 : (0, 2), int
        player B's card
    pr_1 : (0, 1.0), float
        The probability that player A reaches `history`.
    pr_2 : (0, 1.0), float
        The probability that player B reaches `history`.
    pr_c: (0, 1.0), float
        The probability contribution of chance events to reach `history`.
    """
    # if is_chance_node(history): is to be replaced with two functions that are supposed to check for card dealing and flop time  
    #     return chance_util(i_map)
    if is_dealing_chance(history):
        return dealing_util(i_map)


    if is_flop_chance(history):
        return flop_util(i_map,history,p1_card1,p1_card2,p2_card1,p2_card2,pr_1,pr_2,pr_c)



    if is_terminal(history):
        return terminal_util(history, p1_card1,p1_card2,p2_card1, p2_card2)



    n = len(history.split(" "))
    if (n%2 == 0):
        info_set = get_info_set (i_map, p1_card1,p1_card2,history)
    else:
        info_set = get_info_set (i_map,p2_card1,p2_card2,history) 


    strategy = info_set.strategy
    if (n%2==0):
        info_set.reach_pr += pr_1
    else:
        info_set.reach_pr += pr_2


    legal_actions = get_legal_actions(history)
    N_ACTIONS = len(legal_actions) 

    # Counterfactual utility per action.
    action_utils = np.zeros(N_ACTIONS)



    for i, action in enumerate(legal_actions):
        next_history = history + " " + action
        if n%2==0:
            action_utils[i] = -1 * cfr(i_map, next_history,
                                       p1_card1, p1_card2, p2_card1,p2_card2,
                                       pr_1 * strategy[i], pr_2, pr_c)
        else:
            action_utils[i] = -1 * cfr(i_map, next_history,
                                       p1_card1, p1_card2, p2_card1,p2_card2,
                                       pr_1, pr_2 * strategy[i], pr_c)

    # Utility of information set.
    util = sum(action_utils * strategy)
    regrets = action_utils - util
    if n%2==0:
        info_set.regret_sum += pr_2 * pr_c * regrets
    else:
        info_set.regret_sum += pr_1 * pr_c * regrets

    return util


def is_dealing_chance(history):
    """
    There have been no cards dealt, so we just return true for an empty history 

    """
    return history == ""

def is_flop_chance(history):
    """
    should return true if there has been cards dealt,
    so exactly 2 random events and then two bets of the same size 
    """
    hist_parts = history.split(" ")
    if hist_parts.count('r') == 2 and len(hist_parts) > 2: 
        return get_participation_difference(history) == 0

    return False


"""
dealing_util logic is to be replaced with paralel logic 
<----------------------------------------------------------------------------->

"""


def intersection(lst1, lst2):
    return list(set(lst1) & set(lst2))

def calculate_expected_value(local_i_map, combo_1):
    expected_value = 0
    card_combos = list(combinations(deck, 2))
    n_possibilities = 29070  # This is C(20,2) * C(18,2)

   

    for combo_2 in card_combos:
        if len(intersection(combo_1, combo_2)) == 0:
            expected_value += cfr(local_i_map, "r r", list(combo_1)[0], list(combo_1)[1],
                                  list(combo_2)[0], list(combo_2)[1], 1, 1, 1/n_possibilities)
                                  
    game_value = expected_value / n_possibilities

    for _,v in local_i_map.items():
        v.next_strategy()

    return_list = [game_value, local_i_map]

    return return_list

def dealing_util(i_map):
    expected_value = 0
    card_combos = list(combinations(deck, 2))

    with ProcessPoolExecutor(max_workers=30) as executor:
        local_i_map = {}   # Create local dictionary outside the function

        map_list = list(executor.map(calculate_expected_value, [local_i_map] * len(card_combos), card_combos))
        

        local_map_list = []
        value_list = []
        for tuple in map_list:
            local_map_list.append(tuple[1])
            value_list.append(tuple[0])


        global_i_map = {} 
        for map in local_map_list:
            global_i_map.update(map)


    expected_value = sum(value_list)

    return_list = [expected_value,global_i_map]    

    
    
    return return_list
"""

<----------------------------------------------------------------------------->

"""



def flop_util(i_map, history, p1_card1,p1_card2,p2_card1,p2_card2,pr_1,pr_2,pr_c):
    reduced_deck = [x for x in deck if x != p1_card1 and x != p1_card2 and x != p2_card1 and x != p2_card2] #remove cards that have been dealt to players 
    expected_value = 0 
    possible_flops = list(combinations(reduced_deck,3))
    n_possible_flops = len(possible_flops)
    for flop in possible_flops:
        flop = list(flop)
        flop_card_1 = init_deck.card_to_string(flop[0])
        flop_card_2 = init_deck.card_to_string(flop[1])
        flop_card_3 = init_deck.card_to_string(flop[2])
        next_history = history + " r " + flop_card_1 + " " + flop_card_2 + " " + flop_card_3 
    
        return cfr(i_map,next_history,p1_card1,p1_card2,p2_card1,p2_card2,pr_1,pr_2,(pr_c*(1/n_possible_flops)))


def is_terminal(history):
    """
    Returns true if the history is a terminal history.
    """
    hist_parts = history.split()

    n = len(hist_parts)

    if hist_parts[-1] == 'f': # fold is last action 
        return True

    if hist_parts.count('r') == 3: # flop happened, we have a potential showdown 

        post_flop_history = hist_parts[(list_rindex(hist_parts,'r')+1):] 
        for i in range (len(post_flop_history)-1):
            checks = [action for action in post_flop_history if action == 'c']
            if len(checks) == 0:
                if "call" in post_flop_history[-1]:
                    return True 
                return False

            if len(checks) == 1:
                if post_flop_history[-1] == 'c': 
                    return False                    #if there is a check, check if its the last action

                else:
                    #print(history)
                    return "call" in hist_parts[-1]  # raise called, perhaps to be replased with last_action == 'call' since we know we are post-flop 

            if len(checks) == 2: #action checks through, showdown ensues
                return True 


    return False              



def terminal_util(history, p1_card1,p1_card2,p2_card1, p2_card2):
    """
    Returns the utility of a terminal history.


    IMPORTANT : TO BE CHANGED AFTER IMPLEMENTATION OF CALLING AND DIFFERENT BET SIZING 

    
    """
    # n = len(history)
    # card_player = card_1 if n % 2 == 0 else card_2
    # card_opponent = card_2 if n % 2 == 0 else card_1

 

    hist_parts = history.split(" ")
    n = len(hist_parts)


    is_player_1 = n%2==0 

    bet_parts = [bet for bet in hist_parts if bet not in init_deck.card_dictionary and bet != 'r' and bet != 'c' and bet != 'f']
    bets = [int(bet.split('call')[-1]) if 'call' in bet else int(bet.split('b')[-1]) for bet in bet_parts]
    
    p1_participation = bets[::2]
    p2_participation = bets[1::2]


    if hist_parts[-1] == 'f':  # FOLD
        if is_player_1: 
            return sum(p2_participation)   
        else: 
            return (-1)*(sum(p1_participation))


    #otherwise, it's a showdown 
    post_flop_history = hist_parts[(list_rindex(hist_parts,'r')+1):]
    flop_card_1 = init_deck.card_dictionary[post_flop_history[0]]
    flop_card_2 = init_deck.card_dictionary[post_flop_history[1]]
    flop_card_3 = init_deck.card_dictionary[post_flop_history[2]]  

    p1_hand_rank = eval_5cards(p1_card1,p1_card2,flop_card_1,flop_card_2,flop_card_3)
    p2_hand_rank = eval_5cards(p2_card1,p2_card2,flop_card_1,flop_card_2,flop_card_3)
    
    if p1_hand_rank < p2_hand_rank:
        return sum(p2_participation)

    elif p1_hand_rank > p2_hand_rank:
        return (-1)*sum((p1_participation))

    else:
         return 0



def get_info_set(i_map, card1, card2, history):
    """
    Retrieve information set from dictionary.
    """
    key = init_deck.card_to_string(card1) + " " + init_deck.card_to_string(card2) + " " + history
    info_set = None
    N_ACTIONS = len(get_legal_actions(history)) 
    if key not in i_map:
        info_set = InformationSet(key,N_ACTIONS)
        i_map[key] = info_set
        return info_set

    return i_map[key]


class InformationSet():
    def __init__(self, key,N_ACTIONS):
        self.key = key
        self.regret_sum = np.zeros(N_ACTIONS)
        self.strategy_sum = np.zeros(N_ACTIONS)
        self.strategy = np.repeat(1/N_ACTIONS, N_ACTIONS)
        self.reach_pr = 0
        self.reach_pr_sum = 0
        self.N_ACTIONS = N_ACTIONS

    def next_strategy(self):
        self.strategy_sum += self.reach_pr * self.strategy
        self.strategy = self.calc_strategy()
        self.reach_pr_sum += self.reach_pr
        self.reach_pr = 0

    def calc_strategy(self):
        """
        Calculate current strategy from the sum of regret.
        """
        strategy = self.make_positive(self.regret_sum)
        total = sum(strategy)
        if total > 0:
            strategy = strategy / total
        else:
            n = self.N_ACTIONS
            strategy = np.repeat(1/n, n)

        return strategy

    def get_average_strategy(self):
        """
        Calculate average strategy over all iterations. This is the
        Nash equilibrium strategy.
        """
        strategy = self.strategy_sum / self.reach_pr_sum

        # Purify to remove actions that are likely a mistake
        strategy = np.where(strategy < 0.001, 0, strategy)

        # Re-normalize
        total = sum(strategy)
        strategy /= total

        return strategy

    def make_positive(self, x):
        return np.where(x > 0, x, 0)

    def __str__(self):
        strategies = ['{:03.2f}'.format(x)
                      for x in self.get_average_strategy()]
        return '{} {}'.format(self.key.ljust(6), strategies)


def display_results(ev, i_map):
    file = open("cfr_eval_10_iter_parallel_2_rollback.txt", "w")


    file.write('player 1 expected value: {} \n'.format(ev))
    file.write('player 2 expected value: {} \n'.format(-1 * ev))

    
    file.write('player 1 strategies: \n')
    sorted_items = sorted(i_map.items(), key=lambda x: x[0])
    for _, v in filter(lambda x: len(x[0].split(" ")) % 2 == 0, sorted_items):
        file.write(str(v) + '\n')
    
    file.write('player 2 strategies: \n')
    for _, v in filter(lambda x: len(x[0].split(" ")) % 2 == 1, sorted_items):
        file.write(str(v) + '\n')


if __name__ == "__main__":
    main()