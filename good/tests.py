from django.test import TestCase

# Create your tests here.

dict = {b'5': b'4', b'9': b'3', b'26': b'6', b'3': b'4', b'8': b'1', b'12': b'1'}
for i ,j in dict.items():
    print(int(i),':',int(j))