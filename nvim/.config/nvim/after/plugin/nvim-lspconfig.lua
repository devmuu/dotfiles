-- local capabilities = vim.lsp.protocol.make_client_capabilities()
-- capabilities.textDocument.completion.completionItem.snippetSupport = true

-- init = function()
--     vim.opt.signcolumn = 'yes'
-- end

-- config = function()
--     local lsp_defaults = require('lspconfig').util.default_config
--     lsp_defaults.capabilities = vim.tbl_deep_extend(
--         'force',
--         lsp_defaults.capabilities,
--         require('cmp_nvim_lsp').default_capabilities()
--     )
-- end

local lsp_keymaps = {
    desc = 'LSP actions',
    callback = function(event)
        local opts = { buffer = event.buf, noremap = true, silent = true }
        vim.keymap.set('n', 'K', '<cmd>lua vim.lsp.buf.hover()<cr>', opts)
        vim.keymap.set('n', 'gd', '<cmd>lua vim.lsp.buf.definition()<cr>', opts)
        vim.keymap.set('n', 'gD', '<cmd>lua vim.lsp.buf.declaration()<cr>', opts)
        vim.keymap.set('n', 'gi', '<cmd>lua vim.lsp.buf.implementation()<cr>', opts)
        vim.keymap.set('n', 'go', '<cmd>lua vim.lsp.buf.type_definition()<cr>', opts)
        vim.keymap.set('n', 'gr', '<cmd>lua vim.lsp.buf.references()<cr>', opts)
        vim.keymap.set('n', 'gs', '<cmd>lua vim.lsp.buf.signature_help()<cr>', opts)
        vim.keymap.set('n', '<F2>', '<cmd>lua vim.lsp.buf.rename()<cr>', opts)
        vim.keymap.set({ 'n', 'x' }, '<F3>', '<cmd>lua vim.lsp.buf.format({async = true})<cr>', opts)
        vim.keymap.set('n', '<F4>', '<cmd>lua vim.lsp.buf.code_action()<cr>', opts)
    end,
}

vars = {
    vim.api.nvim_create_autocmd('LspAttach', lsp_keymaps)
}
