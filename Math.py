
def two_bytes_to_number(byte_high, byte_low):
    number_result = 256 * byte_high + byte_low
    if number_result >= 32768:
        number_result -= 65536
    return number_result
