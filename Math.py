
def two_bytes_to_number(byte_high, byte_low):
    number_result = 256 * byte_low + byte_high
    if number_result >= 32768:
        number_result -= 65536
    return number_result