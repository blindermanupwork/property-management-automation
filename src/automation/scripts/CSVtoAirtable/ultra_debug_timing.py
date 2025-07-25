#!/usr/bin/env python3
"""
ULTRA DEEP TIMING DEBUGGING - Track function entry/exit and timing
"""

import logging
import datetime
import functools
import threading
import os

logger = logging.getLogger(__name__)

def ultra_timing_debug(func_name_prefix=""):
    """Decorator to add ultra detailed timing to functions"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get timing info
            start_time = datetime.datetime.now()
            timestamp = start_time.strftime('%H:%M:%S.%f')[:12]
            thread_id = threading.current_thread().ident
            process_id = os.getpid()
            
            # Log entry
            func_display_name = f"{func_name_prefix}.{func.__name__}" if func_name_prefix else func.__name__
            logger.critical(f"🕐 ENTER: {func_display_name} at {timestamp} [PID:{process_id}, TID:{thread_id}]")
            
            try:
                # Execute function
                result = func(*args, **kwargs)
                
                # Log successful exit
                end_time = datetime.datetime.now()
                duration = (end_time - start_time).total_seconds()
                end_timestamp = end_time.strftime('%H:%M:%S.%f')[:12]
                logger.critical(f"✅ EXIT:  {func_display_name} at {end_timestamp} [Duration: {duration:.4f}s]")
                
                return result
                
            except Exception as e:
                # Log error exit
                end_time = datetime.datetime.now()
                duration = (end_time - start_time).total_seconds()
                end_timestamp = end_time.strftime('%H:%M:%S.%f')[:12]
                logger.critical(f"❌ ERROR: {func_display_name} at {end_timestamp} [Duration: {duration:.4f}s] - {e}")
                raise
                
        return wrapper
    return decorator

def log_critical_timing(message):
    """Log a critical timing message"""
    timestamp = datetime.datetime.now().strftime('%H:%M:%S.%f')[:12]
    thread_id = threading.current_thread().ident
    process_id = os.getpid()
    logger.critical(f"⏰ TIMING: {message} at {timestamp} [PID:{process_id}, TID:{thread_id}]")