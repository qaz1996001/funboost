
"""
Python 3.7 does not have uuid7, so we implement it ourselves.

uuid7 is more database-friendly than uuid4, similar to the snowflake algorithm.

UUIDv4 provides no way to know the generation time;
UUIDv7 can precisely recover the generation time (millisecond precision).
"""

import time
import secrets
import uuid
from datetime import datetime
import random

def uuid7() -> uuid.UUID:
    """
    RFC 9562 UUIDv7
    """
    # 1. Millisecond timestamp (48 bits)
    ts_ms = int(time.time() * 1000) & ((1 << 48) - 1)

    # 2. Fill the remaining 80 bits with random data
    # Note: We fill the lower 80 bits first, then override Version and Variant via bitwise operations
    rand_payload = secrets.randbits(80)

    # 3. Concatenate timestamp to the high bits
    value = (ts_ms << 80) | rand_payload

    # 4. Set Version 7 (0111)
    # Position: bits 76-79 (counting from right, 0-indexed)
    value &= ~(0xF << 76)  # Clear these 4 bits
    value |= (0x7 << 76)   # Write 0111

    # 5. Set Variant (10xx) - this was the key missing part in the original code
    # Position: bits 62-63
    # RFC 9562 requires Variant to be 2 (i.e., binary 10)
    value &= ~(0x3 << 62)  # Clear these 2 bits
    value |= (0x2 << 62)   # Write 10

    return uuid.UUID(int=value)



def uuid7_fast() -> uuid.UUID:
    ts_ms = int(time.time() * 1000) & ((1 << 48) - 1)
    rand_payload = random.getrandbits(80)  # 5-10x faster than secrets
    value = (ts_ms << 80) | rand_payload
    value &= ~(0xF << 76)
    value |= (0x7 << 76)
    value &= ~(0x3 << 62)
    value |= (0x2 << 62)
    return uuid.UUID(int=value)


# Pre-computed constants
_MASK_48 = (1 << 48) - 1
_MASK_CLEAR = ~(0xF << 76) & ~(0x3 << 62)
_MASK_SET = (0x7 << 76) | (0x2 << 62)

def uuid7_str() -> str:
    """
    Ultra-fast uuid7, returns string directly, skipping uuid.UUID object creation.
    2-3x faster than str(uuid7()).
    """
    value = (int(time.time() * 1000) << 80) | random.getrandbits(80)
    value = (value & _MASK_CLEAR) | _MASK_SET
    h = f'{value:032x}'
    return f'{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:]}'

def parse_uuid7_timestamp(uuid_str: str) -> dict:
    """
    Parse a UUIDv7 string and return a dict containing timestamp information.
    """
    try:
        # 1. Convert to UUID object (automatically handles format validation)
        u = uuid.UUID(uuid_str)
        
        # 2. Check if the version is 7
        if u.version != 7:
            raise ValueError(f"This UUID version is {u.version}, not v7")

        # 3. Extract timestamp
        # UUID is 128 bits total, first 48 bits are the timestamp
        # The int is a 128-bit integer, right-shift by 80 to get the high 48 bits
        ts_ms = u.int >> 80
        
        # 4. Convert to seconds (float)
        ts_seconds = ts_ms / 1000.0
        
        # 5. Generate datetime object
        dt_local = datetime.fromtimestamp(ts_seconds)
        
        return {
            "timestamp_ms": ts_ms,
            "datetime_local": dt_local,
            "iso_format": dt_local.isoformat()
        }

    except ValueError as e:
        return {"error": str(e)}




if __name__ == '__main__':
    # Verify output format
    print("uuid7():", uuid7())
    print("uuid7_fast():", uuid7_fast())
    print("uuid7_str():", uuid7_str())
    print("Parse verification:", parse_uuid7_timestamp(uuid7_str()))
    
    n = 1000000
    print(f"\n=== Performance Comparison ({n} iterations) ===")
    
    # str(uuid7()) - original version
    t = time.time()
    for _ in range(n):
        str(uuid7())
    print(f"str(uuid7()):      {time.time()-t:.3f} sec")
    
    # str(uuid7_fast()) - random version
    t = time.time()
    for _ in range(n):
        str(uuid7_fast())
    print(f"str(uuid7_fast()): {time.time()-t:.3f} sec")
    
    # uuid7_str() - ultra-fast version
    t = time.time()
    for _ in range(n):
        uuid7_str()
    print(f"uuid7_str():       {time.time()-t:.3f} sec  <- fastest")