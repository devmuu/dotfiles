require("luasnip.loaders.from_vscode").lazy_load()
require'luasnip'.filetype_extend("eruby", {"html", "ruby"})
require'luasnip'.filetype_extend("ruby", {"rails"})

local ls = require("luasnip")

return {
    ls.config.set_config{
        history = true,
        updateevents = "TextChanged", "TextChangedI",
        enable_autosnippets = true,
    },

    vim.api.nvim_create_autocmd('LspAttach', {
        desc = 'LuaSnipt actions',
        callback = function(event)
            local opts = { buffer = event.buf }

            vim.keymap.set("i", "<C-k>", function() ls.expand() end, opts)
            -- vim.keymap.set({ "i", "s" }, "<C-l>", function() ls.jump(1) end, opts)
            -- vim.keymap.set({ "i", "s" }, "<C-j>", function() ls.jump(-1) end, opts)
            vim.keymap.set({ "i", "s" }, "<C-e>",
                function()
                    if ls.choice_active() then
                        ls.change_choice(1)
                    end
                end, opts)
        end,
    })

}
