uint64_t pop_count(int64_t row)
{
    int64_t rdi = (row - ((row >> 1) & 0x5555555555555555));
    int64_t rdi_3 = (((rdi >> 2) & 0x3333333333333333) + (rdi & 0x3333333333333333));
    return (((((rdi_3 >> 4) + rdi_3) & 0xf0f0f0f0f0f0f0f) * 0x101010101010101) >> 0x38);
}
