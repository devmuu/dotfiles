-- return{
--     require 'nvim-treesitter'.install({
--         "bash",
--         "c",
--         "dockerfile",
--         "eex",
--         "elixir",
--         "gnuplot",
--         "json",
--         "julia",
--         "lua",
--         "make",
--         "markdown",
--         "markdown_inline",
--         "matlab",
--         "python",
--         "r",
--         "regex",
--         "ruby",
--         "rust",
--         "sql",
--         "toml",
--         "typst",
--         "vim",
--     }):wait(300000)
-- }
local opts = {
        ensure_installed = {
            "bash",
            "c",
            "dockerfile",
            "eex",
            "elixir",
            "gnuplot",
            "json",
            "julia",
            "lua",
            "make",
            "markdown",
            "markdown_inline",
            "matlab",
            "python",
            "r",
            "regex",
            "ruby",
            "rust",
            "sql",
            "toml",
            "typst",
            "vim",
        },
        highlight = {
            enable = true,
            disable = { "" },
            additional_vim_regex_highlighting = { "markdown" },
        },
}

return {
    require('nvim-treesitter.config').setup(opts)
}
