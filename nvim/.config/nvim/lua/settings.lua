-- Settings --

local search_highlight = true

local options = {
    autoindent = true,
    autochdir = true,
    autowrite = true,
    clipboard = 'unnamedplus', -- Copy/paste to system clipboard
    cmdheight = 0,             -- Height value when in cmdmode
    colorcolumn = '80',
    cursorline = true,
    encoding = 'utf-8',
    expandtab = true,
    foldenable = false,
    foldmethod = 'marker',
    foldmarker = '{{{,}}}',
    hidden = true, -- Enable background buffers
    history = 100, -- Remember N lines in history
    hlsearch = true,
    ignorecase = true,
    incsearch = true,
    lazyredraw = true, -- Faster scrolling
    linebreak = true,
    mouse = 'a',       -- Enable mouse support
    number = true,
    relativenumber = false,
    scrolloff = 2,
    shiftwidth = 4,
    sidescroll = 2,
    sidescrolloff = 15,
    signcolumn = 'yes',
    smartindent = true,
    softtabstop = 4,
    spell = false,
    splitright = true,
    swapfile = false, -- Don't use swapfile
    synmaxcol = 240,  -- Max column for syntax highlight
    tabstop = 4,
    termguicolors = true,
    textwidth = 0,
    updatetime = 50,
    wrap = true,
    guifont = { "JetbrainsMono Nerd Font:15" },
}

for k, v in pairs(options) do
    vim.opt[k] = v
end

-- set end of buffer char
vim.wo.fillchars = 'eob: '

-- remove whitespace on save
vim.cmd [[au BufWritePre * :%s/\s\+$//e]]

-- disable nvim intro
vim.opt.shortmess:append "sI"

-- enable nvim-tree lua
vim.g.loaded_netrw = 1
vim.g.loaded_netrwPlugin = 1

-- guicursor style
vim.opt.guicursor = "n-v-c-sm:hor20-Cursor,i-ci-ve:hor20-Cursor-blinkon250-blinkoff250,r-cr-o:hor20-Cursor"
-- vim.opt.guicursor = "n-v-c-sm:hor20-Cursor,i-ci-ve:ver25-Cursor-blinkon250-blinkoff250,r-cr-o:hor20-Cursor"

-- retab file
-- vim.cmd("retab")

-- set listchars
vim.opt.list = true

-- set only tab in listchars
local tab_listchar = {
    tab = '→ ',
}

-- set all in listchars
local all_listchars = {
    tab = '│─',
    space = '·',
    nbsp = '␣',
    trail = '•',
    eol = '↲',
    precedes = '«',
    extends = '»',
}

-- set listchar when open new buffer or window
vim.api.nvim_create_autocmd({ "BufEnter", "BufWinEnter" }, {
    callback = function()
        vim.opt.listchars = tab_listchar
    end
})

-- format options:
-- c: Auto-wrap comments using 'textwidth', inserting the current comment leader automatically.
-- r: Automatically insert the current comment leader after hitting
-- o: Automatically insert the current comment leader after hitting 'o' or 'O' in Normal mode.
-- In case comment is unwanted in a specific place use CTRL-U to quickly delete it.

vim.cmd [[au BufEnter * set fo-=c fo-=r fo-=o]]

-- open terminal in new right vertical split
vim.cmd [[command Term :botright vsplit term://$SHELL]]

vim.cmd [[
    autocmd TermOpen * setlocal listchars= nonumber norelativenumber nocursorline
    autocmd TermOpen * startinsert
    autocmd BufLeave term://* stopinsert
    hi CursorLine ctermbg=237 ctermfg=grey guibg=#3a3a3a cterm=none gui=none
    hi CursorLineNr ctermfg=white ctermbg=magenta guibg=#3a3a3a cterm=none gui=none
    set listchars=tab:→\ ,space:·,nbsp:␣,trail:•,eol:¶,precedes:«,extends:»
]]

vim.api.nvim_exec([[
  augroup YankHighlight
    autocmd!
    autocmd TextYankPost * silent! lua vim.highlight.on_yank{higroup="IncSearch", timeout=200}
  augroup end
]], false)

-- custom filetype
vim.api.nvim_create_autocmd({ "BufNewFile", "BufRead" }, {
    pattern = { "*.swayconfig", "*.sway", "*.sway.conf", "*/sway/sources" },
    callback = function()
        vim.opt["filetype"] = "swayconfig"
    end
})

-- config files from hyprland
vim.api.nvim_create_autocmd({ "BufNewFile", "BufRead" }, {
    pattern = { "*.hypr", "*.hyprlang", "hyprland.conf", "*/hypr/*" },
    callback = function()
        vim.opt["filetype"] = "hyprlang"
        vim.bo.commentstring = "# %s"
    end
})

-- rmpc .ron
vim.api.nvim_create_autocmd({ "BufNewFile", "BufRead" }, {
    pattern = { "*.ron" },
    callback = function()
        vim.opt["filetype"] = "ron"
        vim.bo.commentstring = "// %s"
    end
})

-- markdown
vim.api.nvim_create_autocmd({ "BufNewFile", "BufRead" }, {
    pattern = { "*.md", "*.qmd" },
    callback = function()
        vim.api.nvim_command('syntax match Entity "&amp;" conceal cchar=&')
        vim.o.conceallevel = 2
        vim.o.concealcursor = "nc"
    end
})

-- config files like micro and sway
vim.api.nvim_create_autocmd({ "BufNewFile", "BufRead" }, {
    pattern = { "*.swayconfig", "*.micro" },
    callback = function()
        vim.opt["filetype"] = "config"
    end
})

-- spice files
vim.api.nvim_create_autocmd({ "BufNewFile", "BufRead" }, {
    pattern = { "*.cir", "*.lib", "*.model" },
    callback = function()
        vim.opt["filetype"] = "spice"
    end
})

-- gnuplot files
vim.api.nvim_create_autocmd({ "BufNewFile", "BufRead" }, {
    pattern = { "*.plt" },
    callback = function()
        vim.opt["filetype"] = "gnuplot"
        vim.bo.commentstring = "# %s"
    end
})

-- add commentstring option
vim.api.nvim_create_autocmd("FileType", {
    pattern = { "sql" },
    callback = function()
        vim.bo.commentstring = "-- %s"
    end
})

-- no highlight after search
if search_highlight == false then
    vim.cmd([[
    augroup incsearch-highlight
      autocmd!
      autocmd CmdlineEnter /,\? :set hlsearch
      autocmd CmdlineLeave /,\? :set nohlsearch
    augroup END
    ]], false)
end
