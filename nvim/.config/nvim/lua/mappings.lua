-- ============================================================================
-- Scripts:       mappings.lua
-- Description:   Map keys to use in neovim
-- Software/Tool: lua/neovim
-- ============================================================================

-- ============================================================================
-- aliases
-- ============================================================================

-- vim commands
local cmd = vim.cmd

-- vimscript
local exec = vim.api.nvim_exec

-- set options (global/buffer/windows-scoped)
local opt = vim.opt

-- keymaps in nvim api
local map = vim.api.nvim_set_keymap

-- default options
local opts = {noremap = true, silent = true}

-- leader key
vim.g.mapleader = " "

-- localleader key
vim.g.maplocalleader = "\\"

map("", "<Space>", "Nop", opts)

-- ============================================================================
-- map keys in normal mode
-- ============================================================================

-- save buffer
map("n", "<leader>w", "<cmd>w<cr>", opts)

-- close buffer
map("n", "<leader>q", "<cmd>bdelete<cr>", opts)

-- comment line
-- map("n", "<leader>c", "gcc", {noremap = false})

-- use telescope to search files
map("n", "<leader>f", "<cmd>lua require('telescope.builtin').find_files()<cr>", opts)
map("n", "<leader>g", "<cmd>lua require('telescope.builtin').git_files()<cr>", opts)
map("n", "<leader>s", "<cmd>lua require('telescope.builtin').live_grep()<cr>", opts)
map("n", "<leader>b", "<cmd>lua require('telescope.builtin').buffers()<cr>", opts)
map("n", "<leader>h", "<cmd>lua require('telescope.builtin').help_tags()<cr>", opts)

-- toggle background
map("n", "<localleader>t", "<cmd>lua toggle_background()<cr>", opts)

-- toggle list
-- map("n", "<localleader>t", "<cmd>set list!<cr>", opts)

-- quit window
map("n", "<localleader>q", "<cmd>q<cr>", opts)

-- save and quit window
map("n", "<localleader>w", "<cmd>wq<cr>", opts)

-- esc to stop hlsearch
map("n", "<esc>", "<cmd>set nohlsearch<cr>", opts)

-- source current file
map("n", "<c-s>", "<cmd>so<cr>", opts)

-- toggle nvimtree
map("n", "<c-n>", ":NvimTreeToggle<cr>", opts)

-- move between open buffers
map("n", "<left>", "<cmd>bprevious<cr>", opts)
map("n", "<right>", "<cmd>bnext<cr>", opts)
map("n", "<a-h>", "<cmd>bprevious<cr>", opts)
map("n", "<a-l>", "<cmd>bnext<cr>", opts)

map("n", "J", "mzJ`z", opts)

-- jump 25 lines centering
map("n", "<up>", "18kzz", opts)
map("n", "<down>", "18jzz", opts)

-- center last line view
map("n", "G", "Gzz", opts)

-- center regex search navigation
map("n", "n", "nzz", opts)
map("n", "N", "Nzz", opts)

-- center sentences navigation
map("n", "(", "(zz", opts)
map("n", ")", ")zz", opts)

-- center methods navigation
map("n", "{", "{zz", opts)
map("n", "}", "}zz", opts)

-- center page navigation
map("n", "<c-u>", "<c-u>zz", opts)
map("n", "<c-d>", "<c-d>zz", opts)

-- run code with compile script
map("n", "<c-b>", "<cmd>:w<cr><cmd>silent ! ~/.local/bin/compile %<cr>", opts)

map("n", "<c-c>", "<cmd>:w<cr><cmd>terminal ~/.local/bin/compile %<cr>", opts)

-- move between splits
map("n", "<c-h>", "<c-w>h", opts)
map("n", "<c-j>", "<c-w>j", opts)
map("n", "<c-k>", "<c-w>k", opts)
map("n", "<c-l>", "<c-w>l", opts)

-- run fzf from telescope
map("n", "<c-p>", "<cmd>Telescope find_files hidden=true<cr>", opts)

-- toggle wrap
map("n", "<a-z>", ":set wrap!<cr>", opts)

-- view tests
-- open R terminal
map("n", "<leader>t", "<cmd>lua OpenRTerminal()<cr>", opts)
-- send current line to R terminal
map("n", "<S-CR>", "<cmd>lua SendValue(0)<cr>", opts)
-- clear R terminal
map("n", "<leader>l", "<cmd>lua SendValue(1)<cr>", opts)
-- close R terminal
map("n", "<leader>x", "<cmd>lua SendValue(2)<cr>", opts)

-- disable nvim completion
map("n", "<c-\\>", "<cmd>lua toggle_completion()<cr>", opts)

-- show colorschemes
map("n", "<a-k>", "<cmd>lua require('telescope.builtin').colorscheme()<cr>", opts)

-- switch to terminal split and enter in insert mode
-- map("n", "<c-m>", "<c-w>li", opts)

-- ============================================================================
-- map keys in insert mode
-- ============================================================================

-- enter in normal mode
map("i", "jk", "<esc>", opts)

-- comment line in insert mode
map("i", "<c-c>", "<esc>gccA", { noremap = false })

-- send current line to R terminal
map("i", "<S-CR>", "<cmd>lua SendValue(0)<cr>", opts)

-- switch to terminal split and enter in insert mode
-- map("i", "<c-m>", "<esc><c-w>li", opts)

-- ============================================================================
-- map keys in visal mode
-- ============================================================================

-- move selected lines
map("v", "K", ":m '<-2<cr>gv=gv", opts)
map("v", "J", ":m '>+1<cr>gv=gv", opts)

-- ============================================================================
-- map keys in select mode
-- ============================================================================

-- past copied register in selected text
map("x", "<leader>p", "\"_dP", opts)

-- comment selected lines
map("x", "<Leader>c", "gca<space><esc>0", {noremap = false})

-- ============================================================================
-- map keys in terminal mode
-- ============================================================================

-- exit from terminal in insert mode
map("t", "<Leader>c", "<c-\\><c-n><c-w>h", opts)

