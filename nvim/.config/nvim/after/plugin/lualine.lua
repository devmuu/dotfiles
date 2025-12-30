-- get message when recording a macro
local macro_status = function()
    local reg = vim.fn.reg_recording()
    if reg == "" then return "" end
    return "Macro @" .. reg
end

return {
    require('lualine').setup {
        options = {
            icons_enabled = true,
            theme = 'auto',
            component_separators = { left = '', right = ''},
            section_separators = { left = '', right = ''}, -- █
            disabled_filetypes = {
                statusline = {},
                winbar = {},
            },
            ignore_focus = {},
            always_divide_middle = true,
            globalstatus = false,
            refresh = {
                statusline = 100,
                tabline = 100,
                winbar = 100,
            }
        },
        sections = {
            lualine_a = {'mode'},
            lualine_b = {'diff', macro_status},
            lualine_c = {'branch'},
            lualine_x = {'encoding', 'fileformat'},
            lualine_y = {
                {
                    'filetype',
                    colored = false
                }
            },
            lualine_z = {'progress'}
        },
        inactive_sections = {
            lualine_a = {'mode'},
            lualine_b = {'diff', 'diagnostics'},
            lualine_c = {'branch'},
            lualine_x = {'progress'},
            lualine_y = {},
            lualine_z = {}
        },
        tabline = {},
        winbar = {
            lualine_y = {
                {
                    'buffers',
                    show_filename_only = true,
                    hide_filename_extension = true,
                    show_modified_status = true,
                    mode = 1,
                    max_length = vim.o.columns * 2 / 3,
                    filetype_names = {
                        TelescopePrompt = 'Telescope',
                        dashboard = 'Dashboard',
                        packer = 'Packer',
                        fzf = 'FZF',
                        alpha = 'Alpha'
                    },
                    symbols = {
                        modified = ' ●',
                        alternate_file = '',
                        directory =  '',
                    },
                }
            },
            lualine_z = {'location'},
            lualine_c = {},
            lualine_x = {},
            lualine_b = {},
            lualine_a = {'filename'}
        },
        inactive_winbar = {
            lualine_a = {},
            lualine_b = {},
            lualine_c = {},
            lualine_x = {},
            lualine_y = {},
            lualine_z = {},
        },
        extensions = {},
    }
}
