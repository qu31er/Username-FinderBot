
import random
import asyncio

class UsernameGenerator:
    
    def __init__(self):
        self.vowels = 'aeiouy'
        self.consonants = 'bcdfghjklmnpqrstvwxz'
        self.generated = set()
    
    async def generate_readable(self, length: int):
        """
       
        
        Args:
            length: длина ника (5 или 6)
        
        Yields:
            str: читаемый username
        """
        while True:
            # Чередуем согласные и гласные для читаемости
            username = []
            for i in range(length):
                if i % 2 == 0:
                    username.append(random.choice(self.consonants))
                else:
                    username.append(random.choice(self.vowels))
            
            result = ''.join(username)
            
            # Пропускаем повторы
            if result not in self.generated:
                self.generated.add(result)
                yield result
            
            # Даём время другим задачам
            await asyncio.sleep(0)