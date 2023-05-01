int32_t main(int32_t argc, char** argv, char** envp) __noreturn
{
    int32_t user_status;
    int32_t serial_status;
    int32_t status;
    if (argc == 4)
    {
        int32_t user_width = 0;
        int32_t user_height = 0;
        void* username_img_data = NULL;
        void* user_zbar_img = NULL;

        int32_t serial_width = 0;
        int32_t serial_height = 0;
        void* serial_img_data = NULL;
        void* serial_zbar_img = NULL;

        char digest[0x40];
        strcpy(&digest, argv[1]);
        void sha512;
        SHA512_Init(&sha512);
        SHA512_Update(&sha512, &digest, strlen(argv[1]));
        SHA512_Final(&digest, &sha512);
        
        char qr_data_user[0x40];
        user_status = get_qr_data(argv[2],
            &username_img_data,
            &user_width,
            &user_height,
            &user_zbar_img,
            &qr_data_user,
            0x40);

        char qr_data_serial[0x40];
        serial_status = get_qr_data(argv[3],
            &serial_img_data,
            &serial_width,
            &serial_height,
            &serial_zbar_img,
            &qr_data_serial,
            0x40);

        if ((user_status != 0 && serial_status != 0))
        {
            char err = (serial_width != user_width)
                | (serial_height != user_height)
                | (user_width != user_height)
                | (memcmp(&digest, &qr_data_user, 0x40) != 0)
                | (check_serial(&qr_data_user, &qr_data_serial, 8) == 0);

            void* an_interesting_output = NULL;
            int32_t win = something_interesting(username_img_data, serial_img_data, &an_interesting_output, user_width);

            free(username_img_data);
            free(serial_img_data);
            free(an_interesting_output);

            status = ((uint32_t)(err | ((int8_t)win == 0)));
        }
    }
    else
    {
        printf("Usage: %s <username> <username.p…", *(int64_t*)argv);
    }
    if (((argc != 4 || (argc == 4 && user_status == 0)) || ((argc == 4 && user_status != 0) && serial_status == 0)))
    {
        status = 1;
    }
    exit(status);
    /* no return */
}
