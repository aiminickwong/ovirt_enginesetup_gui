
def AA():
   for i in range(99):
       if i%10 == 0:
           yield i

a=AA()
print a
print a.next()
print a.next()
a.sent(50)
