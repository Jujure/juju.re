uint64_t check(char* input, int64_t len)
{
    int64_t i = 0x14;
    char* cursor = input;
    void* end = &cursor[len];
    void* fsbase;
    int64_t rax = *(int64_t*)((char*)fsbase + 0x28);
    struct context context;
    int64_t* context_ptr = &context;
    for (; i != 0; i = (i - 1))
    {
        *(int64_t*)context_ptr = 0;
        context_ptr = &context_ptr[1];
    }
    // bits = 0x00ffffff
    // visited[0] = 1
    context.bits_queue = 0x100ffffff;
    *(int32_t*)context_ptr = 0;
    uint64_t res;
    if (cursor < end)
    {
        while (true)
        {
            char* next = &cursor[1];
            if (*(int8_t*)cursor > 4)
            {
                res = ((uint64_t)(context.err | 1));
                break;
            }
            int32_t i;
            uint128_t zmm0;
            int128_t arr3_5-9;
            int128_t arr3_1-4;
            switch (*(int8_t*)cursor)
            {
                case 0:
                {
                    int128_t arr1_1-5 = context.visited[1];
                    arr3_1-4 = context.check_board[1];
                    int128_t arr1_5-9 = context.visited[5];
                    int128_t arr1_9-13 = context.visited[9];
                    arr3_5-9 = context.check_board[5];
                    int128_t arr2_1-5 = context.board[1];
                    int32_t r12 = context.visited[5];
                    int32_t rbp_1 = context.visited[9];
                    int128_t arr2_5-9 = context.board[5];
                    int128_t arr2_9-13 = context.board[9];
                    int32_t var_38_1 = context.move;
                    int32_t err1 = (pop_count(((uint64_t)*(int32_t*)((char*)context.j)[0xc])) + pop_count(((uint64_t)context.visited[1])));
                    int32_t err2 = ((err1 + pop_count(((uint64_t)*(int32_t*)((char*)arr1_1-5)[4]))) + pop_count(((uint64_t)*(int32_t*)((char*)arr1_1-5)[8])));
                    int32_t err3 = ((err2 + pop_count(((uint64_t)*(int32_t*)((char*)arr1_1-5)[0xc]))) + pop_count(((uint64_t)r12)));
                    int32_t err4 = ((err3 + pop_count(((uint64_t)*(int32_t*)((char*)arr1_5-9)[4]))) + pop_count(((uint64_t)*(int32_t*)((char*)arr1_5-9)[8])));
                    int32_t err5 = ((err4 + pop_count(((uint64_t)*(int32_t*)((char*)arr1_5-9)[0xc]))) + pop_count(((uint64_t)rbp_1)));
                    int32_t bits = context.bits_queue;
                    int32_t err6;
                    err6 = ((err5 + pop_count(((uint64_t)*(int32_t*)((char*)arr1_9-13)[4]))) + pop_count(((uint64_t)*(int32_t*)((char*)arr1_9-13)[8]))) != 0x90;
                    int32_t err = (err6 | context.err);
                    context.err = err;
                    int128_t var_48_1 = context.check_board[9];
                    zmm0 = ((arr2_9-13 & arr3_1-4) & arr3_5-9);
                    zmm0 = (zmm0 & _mm_bsrli_si128(zmm0, 8));
                    zmm0 = (zmm0 & _mm_bsrli_si128(zmm0, 4));
                    int32_t rax_23;
                    rax_23 = (zmm0 & 0xfff) != 0xfff;
                    int32_t err = (((uint32_t)rax_23) | err);
                    uint32_t flag = 1;
                    context.err = err;
                    if (bits == 0)
                    {
                        int128_t var_48_2 = context.check_board[9];
                        int32_t flag;
                        flag = *(int32_t*)((char*)arr2_9-13)[8] != ((((((((((*(int32_t*)((char*)arr1_9-13)[0xc] ^ arr2_1-5) ^ *(int32_t*)((char*)arr2_1-5)[4]) ^ *(int32_t*)((char*)arr2_1-5)[8]) ^ *(int32_t*)((char*)arr2_1-5)[0xc]) ^ arr2_5-9) ^ *(int32_t*)((char*)arr2_5-9)[4]) ^ *(int32_t*)((char*)arr2_5-9)[8]) ^ *(int32_t*)((char*)arr2_5-9)[0xc]) ^ arr2_9-13) ^ *(int32_t*)((char*)arr2_9-13)[4]);
                        flag = ((uint32_t)flag);
                    }
                    res = ((uint64_t)(err | flag));
                    break;
                    break;
                }
                case 1:  // cycle through instructions
                {
                    cursor = next;
                    context.move = ((context.move + 1) & 3);
                    break;
                }
                // change coordinates and set nth bit of ith element of arr
                // error if bit is already set
                case 2:
                {
                    enum moves op = context.move;
                    int32_t j = context.j;
                    i = context.i;
                    if (op == 0)
                    {
                        j = (j + 1);
                    }
                    else if (op == 1)
                    {
                        i = (i - 1);
                    }
                    else if (op == 2)
                    {
                        j = (j - 1);
                    }
                    else
                    {
                        op = op == 3;
                        i = (i + ((uint32_t)op));
                    }
                    int32_t row;  // get element
                    int64_t i_cpy;
                    if ((j <= 0xb && i <= 0xb))
                    {
                        i_cpy = ((int64_t)i);
                        row = context.visited[i_cpy];
                    }
                    if (((j > 0xb || (j <= 0xb && i > 0xb)) || ((j <= 0xb && i <= 0xb) && (TEST_BITD(row, j)))))
                    {
                        context.err = (context.err | 1);
                        cursor = next;
                    }
                    if (((j <= 0xb && i <= 0xb) && (!(TEST_BITD(row, j)))))
                    {
                        cursor = next;
                        context.j = _mm_unpacklo_epi32(j, i);  // store new indexes
                        context.visited[i_cpy] = (row | ((int32_t)(1 << j)));  // set bit
                    }
                    break;
                }
                // set the nth bit of the ith element of arr2 if lsb of bits is set
                // error if bits is cleared or if bitwise_check(new_element) > 2
                case 3:
                {
                    int32_t bits_queue = context.bits_queue;
                    int64_t i = ((int64_t)context.i);
                    int32_t bits_cleared;
                    bits_cleared = bits_queue == 0;
                    int32_t new_flags = (bits_cleared | context.err);
                    uint64_t row = ((uint64_t)(((bits_queue & 1) << ((int8_t)context.j)) | context.board[i]));  // set bit
                    context.bits_queue = (bits_queue >> 1);  // rshift bits
                    context.board[i] = row;  // save new element of arr2
                    int32_t sub_res;
                    sub_res = pop_count(row);
                    sub_res = sub_res > 2;
                    context.err = (new_flags | ((uint32_t)sub_res));
                    cursor = next;
                    break;
                }
                case 4:
                {
                    int32_t j = ((int32_t)cursor[1]);
                    int64_t i = ((int64_t)cursor[2]);
                    int32_t bits_set;
                    bits_set = context.bits_queue != 0;
                    context.err = (context.err | bits_set);
                    cursor = &cursor[3];
                    int32_t var_198_1 = context.move;
                    int32_t rax_26;
                    uint128_t zmm1;
                    int128_t zmm3;
                    int128_t zmm4;
                    int128_t zmm5;
                    int128_t zmm6;
                    rax_26 = sub_1570(j, i, context.j, context.visited[1], context.visited[5], context.visited[9], context.board[1], context.board[5], context.board[9], context.check_board[1], context.check_board[5], context.check_board[9], i);
                    context.check_board[i] = (context.check_board[i] | (rax_26 << j));
                    break;
                }
            }
            if ((((*(int8_t*)cursor == 3 || *(int8_t*)cursor == 1) || *(int8_t*)cursor == 4) || *(int8_t*)cursor == 2))
            {
                if (cursor >= end)
                {
                    break;
                }
            }
        }
    }
    if ((cursor >= end || (cursor < end && *(int8_t*)cursor <= 4)))
    {
        res = 1;
    }
    *(int64_t*)((char*)fsbase + 0x28);
    if (rax != *(int64_t*)((char*)fsbase + 0x28))
    {
        __stack_chk_fail();
        /* no return */
    }
    return res;
}

