return {
    require('telescope').setup {
        pickers = {
            find_files = {
                follow = true,
            },
            colorscheme = {
                enable_preview = true,
            }
        }
    }
}
