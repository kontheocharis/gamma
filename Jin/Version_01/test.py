
# import enum

from enum import Enum


class Animal(Enum):     # enum.Enum
    dog = 1
    cat = 2
    lion = 3


print(Animal.dog.value)

'''
print("All the enum values are : ")
for Anim in Animal:
    # print(Anim)
    print(Animal)
'''
