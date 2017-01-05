"""
Code to execute two functions simultaneously. Used for recording while playing back another signal.

Function:
    runInParallel(function1, f1args, function2, f2args)

"""


import multiprocessing as mp


def runInSeparateProcess(function, arguments):
    # Creates the pool to run tasks in parallel
    _pool = mp.Pool()

    # Evaluates function asynchronously
    _result = _pool.apply_async(function, arguments)
    
    # Gets the returned data (if any)
    if not _result is None:
        _retValue = _result.get()
    else:
        _retValue = None
    
    _pool.close()
    _pool.join()

    return _retValue

