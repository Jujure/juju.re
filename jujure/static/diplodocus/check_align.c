 uint64_t sub_1570(int32_t j, int32_t i, struct context context)
 {
     int32_t res = 0;
     int32_t *board = context.board;
     int32_t res_flag = 0;
     if ((j <= 0xb && i <= 0xb))
     {
         int32_t r12_1 = (i + 0x79); // ignore this
         int32_t y = -0xb; // First increment
         int32_t rbp_1 = (j + 0xb); // ignore this too
         while (true)
         {
             int32_t y_cpy = (y + 1);
             if (y != 0)
             {
                 int32_t r8 = r12_1; // ignore for now
                 int32_t x = -0xb;  // Second increment
                 int32_t neg = (y >> 0x1f);             // Probably interesting
                 int32_t r11_2 = ((y_cpy * -0xb) + rbp_1); // but I can't seem
                 int32_t y_cpy_cpy = ((neg ^ y) - neg);    // to care enough
                 while (true)
                 {
                     if (x != 0)
                     {
                         int32_t neg = (x >> 0x1f); // Abs value again or
                         int32_t x_cpy = ((neg ^ x) - neg); // something
                         int32_t y_cpy_cpy_cpy = y_cpy_cpy;
                         int32_t count;
                         while (true) // Euclidean algorithm
                         {
                             int32_t y_cpy_cpy;
                             int32_t _;
                             _ = HIGHW(((int64_t)y_cpy_cpy_cpy));
                             y_cpy_cpy = LOWW(((int64_t)y_cpy_cpy_cpy));
                             int32_t mod = (COMBINE(y_cpy_cpy, y_cpy_cpy) % x_cpy);
                             y_cpy_cpy_cpy = x_cpy;
                             count = mod;
                             if (mod == 0)
                             {
                                 break;
                             }
                             x_cpy = mod;
                         }
                         if (x_cpy == 1) // Check if increments are coprime
                         {
                             int32_t row = r8; // Stuff we ignored but seems to
                             int32_t column = r11_2; // be the starting point
                             int32_t m = 0x17;
                             int32_t m_cpy;
                             do // Run through the board using coprime increments
                             {
                                 // Check if we are inside the board
                                 if ((column <= 0xb && row <= 0xb))
                                 {
                                     // Count the bits
                                     count += (board[row] >> column) & 1;
                                 }
                                 column = (column + y);
                                 row = (row + x);
                                 m_cpy = m;
                                 m = (m - 1);
                             } while (m_cpy != 1);

                             // STOP THE COUNT
                             int32_t too_much = count > 2;
                             res_flag = (res_flag | too_much);
                         }
                         if (x == 0xb) // End the while true loops and iterate
                         {
                             break;
                         }
                     }
                     x = (x + 1); // Update increment
                     r8 = (r8 - 0xb);
                 }
                 if (y_cpy == 0xc)
                 {
                     break;
                 }
             }
             y = y_cpy; // Update increment with the next one
         }
         res = res_flag == 0;
     }
     return ((uint64_t)res);
 }

