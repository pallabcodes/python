"""
cProfile wrapper for easy profiling of Python code.
"""

import cProfile
import pstats
import io
from functools import wraps
from typing import Callable, Any


def profile(output_file: str = None, sort_by: str = 'cumulative'):
    """
    Decorator to profile a function using cProfile.
    
    Args:
        output_file: Optional file path to save profiling results
        sort_by: Sort key for stats (default: 'cumulative')
    
    Returns:
        Decorated function that profiles execution
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            profiler = cProfile.Profile()
            profiler.enable()
            
            try:
                result = func(*args, **kwargs)
            finally:
                profiler.disable()
                
                # Create stats
                stats_stream = io.StringIO()
                stats = pstats.Stats(profiler, stream=stats_stream)
                stats.sort_stats(sort_by)
                stats.print_stats()
                
                # Print or save results
                if output_file:
                    with open(output_file, 'w') as f:
                        f.write(stats_stream.getvalue())
                else:
                    print(stats_stream.getvalue())
            
            return result
        return wrapper
    return decorator


def profile_context_manager():
    """
    Context manager for profiling code blocks.
    
    Usage:
        with profile_context_manager() as profiler:
            # Your code here
            pass
    """
    class ProfileContext:
        def __init__(self):
            self.profiler = cProfile.Profile()
            self.stats = None
        
        def __enter__(self):
            self.profiler.enable()
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.profiler.disable()
            stats_stream = io.StringIO()
            self.stats = pstats.Stats(self.profiler, stream=stats_stream)
            self.stats.sort_stats('cumulative')
            self.stats.print_stats()
            print(stats_stream.getvalue())
    
    return ProfileContext()

