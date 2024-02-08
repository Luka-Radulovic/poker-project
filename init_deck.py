import arrays






primes = [23, 29, 31, 37, 41]
relevant_suits = [8,9,10,11,12]
from itertools import combinations 


def intersection(lst1, lst2):
    return list(set(lst1) & set(lst2))


card_dictionary = {} 

def init_deck(deck):
    n = 0
    suit = 0x8000

  

    for i in range(4):
        
        for j in range(5):
            deck[n] = primes[j] | (relevant_suits[j] << 8) | suit | (1 << (16 + relevant_suits[j]))
            n += 1
        suit >>= 1


def card_to_string(card):
    ranks =  "23456789TJQKA";
    r = (card >> 8) & 0xF 
    if card & 0x8000:
        suit = 'c'
    elif card & 0x4000:
        suit = 'd'
    elif card & 0x2000:
        suit = 'h'
    else: 
        suit = 's'
    card_str = ranks[r] + suit
    return card_str

deck = [0] * (20)
init_deck(deck)
translated_deck = []
for card in deck:
    translated_deck.append(card_to_string(card))


card_dictionary = dict(zip(translated_deck,deck))


if __name__ == "__main__":
   print(deck)
   print(translated_deck)
   print(card_dictionary)
