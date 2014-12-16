import time
def follow(thefile, target):
    #thefile.seek(0,2) # Go to the end of the file
    while True:
        line = thefile.readline()
        if not line:
            time.sleep(0.1) # Sleep briefly
            continue
        print target
        target.send(line)

def coroutine(func):
    def start(*args,**kwargs):
        cr = func(*args,**kwargs)
        cr.next()
        return cr
    return start

@coroutine
def printer():
    while True:
        line = (yield)
        print line

f = open("access-log")
follow(f, printer())
