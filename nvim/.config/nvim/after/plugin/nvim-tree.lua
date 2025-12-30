return {
    require("nvim-tree").setup({
        sort = {
            sorter = "case_sensitive",
        },
        view = {
            width = 30,
            float = {
                enable = false,
                quit_on_focus_loss = true,
                open_win_config = {
                    width = 50,
                }
            }
        },
        renderer = {
            group_empty = true,
        },
        filters = {
            dotfiles = true,
        },
        actions = {
            open_file = {
                quit_on_open = false,
            }
        }
    })
}
