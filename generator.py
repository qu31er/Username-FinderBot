import random

VOWELS = 'AEIOU'
CONSONANTS = 'BCDFGHJKLMNPQRSTVWXYZ'

def generate_readable(length):
    """
    Генерирует читаемый username (чередование гласных/согласных).
    """
    if length == 5:
        pattern = random.choice(['CVCVC', 'VCVCV'])
    else:  # length == 6
        pattern = random.choice(['CVCVCV', 'VCVCVC'])
    
    result = ''
    for ch in pattern:
        if ch == 'C':
            result += random.choice(CONSONANTS)
        else:
            result += random.choice(VOWELS)
    return result

def generate_combination(length):
    """
    Генерирует случайную комбинацию букв (без фильтра).
    """
    letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    return ''.join(random.choice(letters) for _ in range(length))

def generate_batch(length, count=100, readable=True):
    """
    Генерирует пачку username'ов.
    """
    usernames = set()
    attempts = 0
    max_attempts = count * 10
    
    while len(usernames) < count and attempts < max_attempts:
        attempts += 1
        if readable:
            nick = generate_readable(length)
        else:
            nick = generate_combination(length)
        usernames.add(nick)
    
    return list(usernames)[:count]