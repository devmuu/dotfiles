return {
    -- I have a separate config.mappings file where I require which-key.
    -- With lazy the plugin will be automatically loaded when it is required somewhere
    {
        "folke/which-key.nvim",
        lazy = true
    },

    {
        "nvim-neorg/neorg",
        -- lazy-load on filetype
        ft = "norg",
        -- options for neorg. This will automatically call `require("neorg").setup(opts)`
        opts = {
            load = {
                ["core.defaults"] = {},
            },
        },
    },

    -- if some code requires a module from an unloaded plugin, it will be automatically loaded.
    -- So for api plugins like devicons, we can always set lazy=true
    {
        "nvim-tree/nvim-web-devicons",
        lazy = true
    },

    -- mini pairs
    {
        'echasnovski/mini.nvim', version = false
    },

    -- nvim-tree
    {
        "nvim-tree/nvim-tree.lua",
        lazy = false,
    },

    -- treesitter
    {
        "nvim-treesitter/nvim-treesitter",
        build = ':TSUpdate',
        lazy = false,
    },

    -- telescope
    {
        "nvim-telescope/telescope.nvim",
        -- tag = "0.2.0",
        dependencies = { "nvim-lua/plenary.nvim" }
    },

    -- vimtex
    -- {
    --     "lervag/vimtex",
    --     lazy = false,
    --     init = function()
    --         -- VimTeX configuration goes here
    --         vim.g.vimtex_view_method = "zathura"
    --         vim.g.vimtex_compiler_method = "generic"
    --         vim.g.vimtex_compiler_generic = { command = "make distrobox" }
    --         vim.g.Tex_DefaultTargetFormat = "pdf"
    --         vim.g.vimtex_view_enabled = 1
    --         vim.g.vimtex_view_automatic = 1
    --         vim.g.vimtex_view_general_viewer = "zathura"
    --         vim.g.vimtex_compiler_progname = "nvr"
    --         vim.g.tex_flavor = "latex"
    --     end
    -- },

    -- fzf
    {
        "junegunn/fzf",
        build = "./install --bin"
    },

    -- lualine
    {
        'nvim-lualine/lualine.nvim',
        dependencies = { 'nvim-tree/nvim-web-devicons' }
    },

    -- vim-surround
    {
        'tpope/vim-surround',
    },

    -- mason lsp installer
    {
        'williamboman/mason.nvim',
        lazy = false,
        config = function()
            require("mason").setup()
        end,
    },

    {
        'williamboman/mason-lspconfig.nvim',
        lazy = false,
        config = function()
            require("mason").setup()
        end,
    },

    -- lsp nvim
    {
        'neovim/nvim-lspconfig',
        -- cmd = {'LspInfo', 'LspInstall', 'LspStart'},
        -- event = {'BufReadPre', 'BufNewFile'},
        dependencies = {
            { 'hrsh7th/cmp-nvim-lsp' },
            { 'saadparwaiz1/cmp_luasnip' },
            { 'williamboman/mason.nvim' },
            { 'williamboman/mason-lspconfig.nvim' },
        },
    },

    -- lua snippets
    {
        "L3MON4D3/LuaSnip",
        version = "v2",
        build = "make install_jsregexp",
        dependencies = { "rafamadriz/friendly-snippets" },
    },

    -- lsp autocompletion
    {
        'hrsh7th/nvim-cmp',
        event = { "InsertEnter", "CmdlineEnter" },
    },

    -- autocompletion via lsp
    {
        'hrsh7th/cmp-nvim-lsp',
    },

    -- autocompletion via buffer
    {
        'hrsh7th/cmp-buffer'
    },

    -- autocompletion via path
    {
        'hrsh7th/cmp-path'
    },

    -- eletro colors
    {
        "devmuu/eletro-colors",
        lazy = false
    },
}
