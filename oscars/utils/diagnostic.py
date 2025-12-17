import time, functools, logging
log = logging.getLogger("timer")

def timed(name=None, size_fn=None):
    def deco(fn):
        @functools.wraps(fn)
        def wrap(*a, **kw):
            t0 = time.perf_counter()
            out = fn(*a, **kw)
            diff_time = (time.perf_counter() - t0)
            n  = None
            if size_fn:
                try: n = size_fn(*a, **kw, out=out)
                except Exception: pass
            log.info("TIMER | %s | %.3fs%s", name or fn.__name__, diff_time,
                     f" | per_row={diff_time/max(n,1):.6f}s (n={n})" if isinstance(n,(int,float)) else "")
            return out
        return wrap
    return deco


@timed(size_fn=lambda *a, out=None, **kw: len(out) if hasattr(out, "__len__") else None)
def extract_pairs(): ...
