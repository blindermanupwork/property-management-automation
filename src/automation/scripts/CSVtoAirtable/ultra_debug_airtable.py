#!/usr/bin/env python3
"""
ULTRA DEEP DEBUGGING - Monkey patch pyairtable to track EVERY record creation
This will catch ANY Airtable record creation regardless of which script calls it
"""

import logging
import traceback
import datetime
import os
import threading
from functools import wraps

# Set up ultra detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ultra_debug_wrapper(original_method, method_name):
    """Wrap any method with ultra detailed debugging"""
    @wraps(original_method)
    def wrapper(*args, **kwargs):
        # Get current time with microseconds
        timestamp = datetime.datetime.now().strftime('%H:%M:%S.%f')[:12]
        
        # Get thread and process info
        thread_id = threading.current_thread().ident
        process_id = os.getpid()
        
        # Get call stack
        stack = traceback.extract_stack()
        call_stack = []
        for frame in stack[-10:]:  # Last 10 frames
            call_stack.append(f"{frame.filename}:{frame.lineno} in {frame.name}")
        
        # Log the call
        logger.critical(f"🔍 ULTRA DEEP: {method_name} called at {timestamp}")
        logger.critical(f"   Process: {process_id}, Thread: {thread_id}")
        logger.critical(f"   Args: {len(args)} args, {len(kwargs)} kwargs")
        
        # For create operations, log what's being created
        if 'create' in method_name.lower():
            logger.critical(f"🚨 RECORD CREATION DETECTED: {method_name}")
            logger.critical(f"   Call Stack:")
            for i, frame in enumerate(call_stack):
                logger.critical(f"     {i}: {frame}")
            
            # Log the data being created
            if args:
                if len(args) > 1:
                    data = args[1]  # Usually the data is the second argument
                    if isinstance(data, (list, dict)):
                        logger.critical(f"   Data being created: {data}")
                        
                        # For batch creates, log each record
                        if isinstance(data, list):
                            for i, record in enumerate(data):
                                if isinstance(record, dict) and 'fields' in record:
                                    uid = record['fields'].get('Reservation UID', 'unknown')
                                    prop = record['fields'].get('Property ID', ['unknown'])
                                    logger.critical(f"     Record {i+1}: UID={uid}, Property={prop}")
                                elif isinstance(record, dict):
                                    uid = record.get('Reservation UID', 'unknown')
                                    prop = record.get('Property ID', ['unknown'])
                                    logger.critical(f"     Record {i+1}: UID={uid}, Property={prop}")
                        elif isinstance(data, dict):
                            uid = data.get('Reservation UID', 'unknown')
                            prop = data.get('Property ID', ['unknown'])
                            logger.critical(f"     Single Record: UID={uid}, Property={prop}")
        
        # Execute the original method
        try:
            result = original_method(*args, **kwargs)
            
            if 'create' in method_name.lower():
                logger.critical(f"✅ {method_name} completed successfully at {datetime.datetime.now().strftime('%H:%M:%S.%f')[:12]}")
                
            return result
        except Exception as e:
            logger.critical(f"❌ {method_name} failed: {e}")
            raise
    
    return wrapper

def monkey_patch_pyairtable():
    """Monkey patch pyairtable to add ultra debugging"""
    try:
        # Import pyairtable
        from pyairtable import Table
        
        # Patch all create methods
        original_create = Table.create
        original_batch_create = Table.batch_create
        original_batch_update = Table.batch_update
        original_update = Table.update
        
        Table.create = ultra_debug_wrapper(original_create, "Table.create")
        Table.batch_create = ultra_debug_wrapper(original_batch_create, "Table.batch_create")
        Table.batch_update = ultra_debug_wrapper(original_batch_update, "Table.batch_update")
        Table.update = ultra_debug_wrapper(original_update, "Table.update")
        
        logger.critical("🔍 ULTRA DEBUG: pyairtable monkey patched successfully!")
        
    except Exception as e:
        logger.error(f"Failed to monkey patch pyairtable: {e}")

# Auto-patch when this module is imported
monkey_patch_pyairtable()