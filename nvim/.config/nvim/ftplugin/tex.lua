local map = vim.api.nvim_set_keymap
local opts = {noremap = true, silent = true}

-- show table of contents
map("n", "<TAB>", "<Cmd>VimtexTocToggle<CR>", opts)

-- compile with vimtex
map("n", "<F5>", "<Cmd>w<cr><cmd>VimtexCompile<CR>", opts)

-- view file with vimtex
map("n", "<F6>", "<Cmd>VimtexView<CR>", opts)

-- some escapes and latex shortcuts
vim.cmd [[
augroup latex_file
  inoremap <c-k> \textit{}<esc>i
  inoremap <c-b> \textbf{}<esc>i
  inoremap <c-d> \dfrac{}{}<esc>2hi
  inoremap <c-s> _{}<esc>hci{
  inoremap <c-e> $$  $$<esc>2hi
  inoremap 'a \'a
  inoremap 'e \'e
  inoremap 'i \'i
  inoremap 'o \'o
  inoremap 'u \'u
  inoremap `a \`a
  inoremap ~a \~a
  inoremap ~o \~o
  inoremap ^a \^a
  inoremap ^e \^e
  inoremap ^o \^o
  inoremap 'c \c{c}
  inoremap 'A \'a
  inoremap 'E \'E
  inoremap 'I \'I
  inoremap 'O \'O
  inoremap 'U \'U
  inoremap `A \`A
  inoremap ~A \~A
  inoremap ~O \~O
  inoremap ^A \^A
  inoremap ^E \^E
  inoremap ^O \^O
  inoremap 'C \c{C}
  inoremap ;doc \begin{document}<CR>\end{document}<esc>Vk3<o<space>
augroup END
]]
