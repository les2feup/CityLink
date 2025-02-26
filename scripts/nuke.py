# ***WARNING***
# Running this file  will delete all files and directories from the micropython device it's running on
# If you run  keep_this=False it will delete this file as well.

# see https://docs.micropython.org/en/latest/library/os.html for os function list

import os


def _delete_all(directory='.', keep_this=True):
    try:
        import machine
    except:
        # not a micropython board so exit gracefully
        print('Not a micro-python board! Leaving it well alone.')
        return
    for fi in os.ilistdir(directory):
        fn, ft = fi[0:2] # can be 3 or 4 items returned!
        if keep_this and fn == '_nuke.py':
            continue
        fp = '%s/%s' % (directory, fn)
        print('removing %s' % fp) 
        if ft == 0x8000:
            os.remove(fp)
        else:
            _delete_all(fp)
            os.rmdir(fp)


_delete_all()
