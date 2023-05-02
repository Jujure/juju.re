else
{
    char* pos_ptr = strchr("abcdefghjklmnpqrstuvwxyz", input[state_index]);
    if (pos_ptr != NULL)
    {
        int64_t pos = pos_ptr - "abcdefghjklmnpqrstuvwxyz";
        int32_t remainder = pos % 4;
        char* permutation_array = &permutations[pos / 4];
        while (true)
        {
            if (remainder < 1)
                break;
            remainder -= 1;

            char state_copy[0x36];
            char* state_copy_ptr = &state_copy;

            char* state_ptr_1 = &state;

            int64_t i = 0x36;
            for (; i != 0; i -= 1)
            {
                *state_copy_ptr = *state_ptr_1;
                state_copy_ptr += 1;
                state_ptr_1 += 1;
            }
            do
            {
                char elem = state_copy[permutation_array[i]];
                state[i] = elem;
                i += 1
            } while (i != 0x36);
        }
        state_index += 1;
        continue;
    }
}