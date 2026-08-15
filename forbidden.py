import re

# ==================== СТАТИЧЕСКИЕ СПИСКИ ЗАПРЕЩЁННЫХ КОМБИНАЦИЙ ====================

# 1. Клавиатурные ряды (Qwerty)
KEYBOARD_ROWS = [
    'QWERTYUIOP', 'ASDFGHJKL', 'ZXCVBNM',
    'POIUYTREWQ', 'LKJHGFDSA', 'MNBVCXZ'
]

# 2. Алфавитные последовательности (только 5 и 6 букв)
ALPHABET_SEQUENCES = [
    # 5 букв
    'ABCDE', 'BCDEF', 'CDEFG', 'DEFGH', 'EFGHI', 'FGHIJ', 'GHIJK', 'HIJKL', 'IJKLM', 'JKLMN',
    'KLMNO', 'LMNOP', 'MNOPQ', 'NOPQR', 'OPQRS', 'PQRST', 'QRSTU', 'RSTUV', 'STUVW', 'TUVWX',
    'UVWXY', 'VWXYZ', 'EDCBA', 'FEDCB', 'GFEDC', 'HGFED', 'IHGFE', 'JIHGF', 'KJIHG', 'LKJIH',
    'MLKJI', 'NMLKJ', 'ONMLK', 'PONML', 'QPONM', 'RQPON', 'SRQPO', 'TSRQP', 'UTSRQ', 'VUTSR',
    'WVUTS', 'XWVUT', 'YXWVU', 'ZYXWV',
    # 6 букв
    'ABCDEF', 'BCDEFG', 'CDEFGH', 'DEFGHI', 'EFGHIJ', 'FGHIJK', 'GHIJKL', 'HIJKLM', 'IJKLMN',
    'JKLMNO', 'KLMNOP', 'LMNOPQ', 'MNOPQR', 'NOPQRS', 'OPQRST', 'PQRSTU', 'QRSTUV', 'RSTUVW',
    'STUVWX', 'TUVWXY', 'UVWXYZ', 'FEDCBA', 'GFEDCB', 'HGFEDC', 'IHGFED', 'JIHGFE', 'KJIHGF',
    'LKJIHG', 'MLKJIH', 'NMLKJI', 'ONMLKJ', 'PONMLK', 'QPONML', 'RQPONM', 'SRQPON', 'TSRQPO',
    'UTSRQP', 'VUTSRQ', 'WVUTSR', 'XWVUTS', 'YXWVUT', 'ZYXWVU'
]

# 3. Повторяющиеся паттерны (только 5 и 6 букв)
REPEATED_PATTERNS = [
    # 5 букв
    'AAAAA', 'BBBBB', 'CCCCC', 'DDDDD', 'EEEEE', 'FFFFF', 'GGGGG', 'HHHHH',
    'IIIII', 'JJJJJ', 'KKKKK', 'LLLLL', 'MMMMM', 'NNNNN', 'OOOOO', 'PPPPP',
    'QQQQQ', 'RRRRR', 'SSSSS', 'TTTTT', 'UUUUU', 'VVVVV', 'WWWWW', 'XXXXX',
    'YYYYY', 'ZZZZZ',
    # 6 букв
    'AAAAAA', 'BBBBBB', 'CCCCCC', 'DDDDDD', 'EEEEEE', 'FFFFFF', 'GGGGGG', 'HHHHHH',
    'IIIIII', 'JJJJJJ', 'KKKKKK', 'LLLLLL', 'MMMMMM', 'NNNNNN', 'OOOOOO', 'PPPPPP',
    'QQQQQQ', 'RRRRRR', 'SSSSSS', 'TTTTTT', 'UUUUUU', 'VVVVVV', 'WWWWWW', 'XXXXXX',
    'YYYYYY', 'ZZZZZZ'
]

# 4. Очевидные слова (только 5-6 букв)
OBVIOUS_WORDS = [
    'ADMIN', 'USER', 'GUEST', 'TEST', 'DEMO', 'HELLO', 'WORLD',
    'PHONE', 'EMAIL', 'SECRET', 'LOGIN', 'SIGNUP', 'GOOGLE', 'APPLE',
    'MICRO', 'SOFT', 'LINUX', 'WINDOWS', 'MACOS', 'ANDROID', 'WINDOW',
    'MOUSE', 'KEYBOARD', 'PASSWORD', 'SAMSUNG', 'XIAOMI', 'IPHONE',
    'FACEBOOK', 'INSTAGRAM', 'TWITTER', 'YOUTUBE', 'TELEGRAM', 'WHATSAPP',
    'SNAPCHAT', 'TIKTOK', 'NETFLIX', 'SPOTIFY', 'AMAZON', 'MICROSOFT',
    'PRINTER', 'SCANNER', 'SPEAKER', 'CAMERA', 'MONITOR', 'HOCKEY',
    'TENNIS', 'SOCCER', 'CRICKET', 'RUGBY', 'GOLF', 'SWIMMING',
    'RUNNING', 'CYCLING', 'SKIING', 'SURFING', 'CLIMBING', 'YOGA',
    'DANCING', 'SINGING', 'ACTING', 'DRAWING', 'PAINTING', 'PHOTOGRAPHY',
    'WRITING', 'READING', 'CODING', 'HACKING', 'CYBER', 'SECURITY',
    'PRIVACY', 'CRYPTO', 'BITCOIN', 'ETHEREUM', 'BLOCKCHAIN', 'METAVERSE',
    'VIRTUAL', 'REALITY', 'INTELLIGENCE', 'MACHINE', 'LEARNING', 'NEURAL',
    'NETWORK', 'SERVER', 'DATABASE', 'TOKEN', 'MUSIC', 'MOVIE', 'GAME',
    'SPORT', 'FOOTBALL', 'BASKETBALL', 'BASEBALL', 'SKATEBOARD'
]

# 5. Только гласные (5-6 букв)
ONLY_VOWELS = [
    'AAAAA', 'AAAAAA', 'EEEEE', 'EEEEEE', 'IIIII', 'IIIIII',
    'OOOOO', 'OOOOOO', 'UUUUU', 'UUUUUU', 'AEIOU', 'UOIEA',
    'AEEIU', 'OUAIA', 'EUAIO', 'IAOUE'
]

# 6. Популярные никнеймы (почти гарантированно заняты)
POPULAR_NICKS = [
    'BOT', 'TELEGRAM', 'TGRAM', 'TG', 'SUPPORT', 'HELP'
]

# 7. Имена (популярные, почти всегда заняты)
COMMON_NAMES = [
    'ALEX', 'MAX', 'JOHN', 'MIKE', 'DAVID', 'JAMES', 'ROBERT', 'MICHAEL',
    'WILLIAM', 'JOSEPH', 'THOMAS', 'CHARLES', 'CHRISTOPHER', 'DANIEL',
    'MATTHEW', 'ANTHONY', 'DONALD', 'MARK', 'PAUL', 'STEVEN', 'ANDREW',
    'KENNETH', 'JOSHUA', 'KEVIN', 'BRIAN', 'GEORGE', 'EDWARD', 'RONALD',
    'TIMOTHY', 'JASON', 'JEFFREY', 'FRANK', 'GARY', 'ERIC', 'STEPHEN',
    'JONATHAN', 'LARRY', 'JUSTIN', 'SCOTT', 'BRANDON', 'BENJAMIN',
    'SAMUEL', 'GREGORY', 'ALEXANDER', 'PATRICK', 'JACK', 'DENNIS',
    'JERRY', 'TYLER', 'AARON', 'JOSE', 'NATHAN', 'ADAM', 'HENRY',
    'ZACHARY', 'TRISTAN', 'DYLAN', 'HUNTER', 'JORDAN', 'CAMERON',
    'LOGAN', 'EMMA', 'OLIVIA', 'AVA', 'ISABELLA', 'SOPHIA', 'MIA',
    'CHARLOTTE', 'AMELIA', 'HARPER', 'EVELYN', 'ABIGAIL', 'EMILY',
    'ELIZABETH', 'MILLA', 'ELEANOR', 'HANNAH', 'LILY', 'GRACE',
    'SOFIA', 'AURORA', 'SCARLETT', 'CHLOE', 'ISLA', 'NORA'
]

# ==================== ФУНКЦИЯ ПРОВЕРКИ ====================

def is_forbidden(username):
    """
    Проверяет, запрещён ли username.
    Возвращает True, если ник НЕЛЬЗЯ проверять.
    """
    s = username.upper()
    n = len(s)
    
    # ❌ Отсекаем всё, что не 5 или 6 символов
    if n not in (5, 6):
        return True
    
    # ❌ Если есть что-то кроме букв — отсекаем
    if not s.isalpha():
        return True
    
    # 1. Проверка по статическим спискам
    if s in REPEATED_PATTERNS:
        return True
    if s in OBVIOUS_WORDS:
        return True
    if s in ONLY_VOWELS:
        return True
    if s in POPULAR_NICKS:
        return True
    if s in COMMON_NAMES:
        return True
    
    # 2. Клавиатурные ряды
    for row in KEYBOARD_ROWS:
        if s in row:
            return True
        if s[::-1] in row:
            return True
    
    # 3. Алфавитные последовательности
    if s in ALPHABET_SEQUENCES:
        return True
    
    # 4. Циклические повторы (ABABAB, ABCABC)
    for i in range(1, n // 2 + 1):
        if n % i == 0 and s == s[:i] * (n // i):
            return True
    
    # 5. Паттерны AABB, ABBA, AAA
    if re.search(r'(.)\1(.)\2', s):  # AABB
        return True
    if re.search(r'(.)(.)\2\1', s):  # ABBA
        return True
    if re.search(r'(.)\1{2,}', s):   # три подряд (AAA)
        return True
    
    # 6. Только гласные или только согласные
    vowels = set('AEIOU')
    if all(c in vowels for c in s):
        return True
    if not any(c in vowels for c in s):
        return True
    
    return False

# ==================== ДЛЯ ОТЛАДКИ ====================

if __name__ == '__main__':
    test_nicks = [
        'AAAAA', 'HELLO', 'QWERTY', 'BATUVI', 'APPLE', 'ABCDE',
        'RANDOM', 'ABC', 'ABCD', 'ABCDEFG', 'A1B2C', 'ALEX',
        'RENAPI', 'KOLUME', 'JOHN', 'BANANA', 'PYTHON', 'JAVA',
        'CODING', 'ADMIN', 'USER', 'TEST', 'DEMO'
    ]
    
    print('🧪 Тестирование фильтра запрещённых комбинаций\n' + '='*50)
    
    for nick in test_nicks:
        status = '❌ ЗАПРЕЩЁН' if is_forbidden(nick) else '✅ МОЖНО ПРОВЕРЯТЬ'
        print(f'{nick:10} → {status}')
    
    print('='*50)
    print(f'📊 Всего запрещённых в списках:')
    print(f'  • Повторяющиеся: {len(REPEATED_PATTERNS)}')
    print(f'  • Очевидные слова: {len(OBVIOUS_WORDS)}')
    print(f'  • Только гласные: {len(ONLY_VOWELS)}')
    print(f'  • Популярные ники: {len(POPULAR_NICKS)}')
    print(f'  • Имена: {len(COMMON_NAMES)}')
    print(f'  • Алфавитные: {len(ALPHABET_SEQUENCES)}')