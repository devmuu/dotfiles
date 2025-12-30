-- some escapes and latex shortcuts
vim.cmd [[
augroup bibtex_file
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
augroup END
]]
