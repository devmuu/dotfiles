local cmp = require('cmp')
local ls = require('luasnip')
local split_mode = 'simple'

local split_format = function(entry, vim_item)
    if split_mode == 'simple' then
        vim_item.kind = string.format('')
    else
        vim_item.kind = string.format('%s %s', vim_item.kind, entry.source.name)
    end

    return vim_item
end

return {
    cmp.setup({
        snippet = {
            expand = function(args)
                ls.lsp_expand(args.body)
            end,
        },

        sources = {
            { name = 'nvim_lsp' },
            { name = 'luasnip' },
            { name = "buffer" },
            { name = "path" },
        },

        window = {
            completion = cmp.config.window.bordered(),
            documentation = cmp.config.window.bordered(),
        },

        mapping = cmp.mapping.preset.insert({
            ['<C-m>'] = cmp.mapping.select_next_item(),
            ['<C-n>'] = cmp.mapping.select_prev_item(),
            ['<C-b>'] = cmp.mapping.scroll_docs(-4),
            ['<C-f>'] = cmp.mapping.scroll_docs(4),
            ['<C-Space>'] = cmp.mapping.complete(),
            ['<C-e>'] = cmp.mapping.abort(),
            ['<Tab>'] = cmp.mapping.confirm({ select = true }),
            -- ['<C-y>'] = cmp.mapping({
            --     i = function ()
            --         if cmp.visible() then
            --             cmp.abort()
            --             toggle_completion()
            --         else
            --             cmp.complete()
            --             toggle_completion()
            --         end
            --     end,
            -- }),
            -- ['<CR>'] = cmp.mapping({
            --     i = function(fallback)
            --         if cmp.visible() then
            --             cmp.confirm({ behavior = cmp.ConfirmBehavior.Replace, select = false })
            --             toggle_completion()
            --         else
            --             fallback()
            --         end
            --     end,
            -- }),
        }),

        completion = {
            completeopt = 'menu,menuone,noinsert',
        },

        formatting = {
            format = split_format
        },
    })
}
